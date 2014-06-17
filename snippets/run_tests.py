import os
import re
import csv
import sys
import time
import glob
import shutil
import getopt
import xml.sax.saxutils
import subprocess
from subprocess import Popen, PIPE, STDOUT
import signal
import threading
import time

from config import Config
from string import Template
from xml.dom import minidom
import traceback
from decimal import *
import enum
from enum import Enum

from traffic import *

ExitCode = Enum('OK', 'Error', 'Skipped')
exitCode = ExitCode.OK # Exit code
timeOut = 3600 # Default value for timeout

class Test:
    class Status:
        PASSED, FAILED, IGNORED = range(3)

    testName = ""
    testError = []
    status = None
    def __init__(self, testName):
        self.testName = testName

def get_branch_name(basedir):
    branch = os.getenv("BRANCH")
    return branch

def get_config(basedir):
    cfg = None
    branch_cfg = None

    default_file = basedir + '/test_runner/default.ini'
    default_cfg = Config(file(default_file))

    branch = get_branch_name(basedir)
    branch_file = basedir + '/test_runner/' + branch + '.ini'

    if os.path.isfile(branch_file):
        branch_cfg  = Config(file(branch_file))

    if branch_cfg == None:
        logEvent('INFO: Branch Specific Config Doesn\'t Exists: ' + branch_file + ' Using ' + default_file )
        cfg = default_cfg
    else:
        logEvent('INFO: Config Version\'s: %s(%s) - %s(%s)' % (default_file, default_cfg.dev.version, branch_file, branch_cfg.dev.version) )
        if default_cfg.dev.version != branch_cfg.dev.version:
            logEvent('INFO: Versions doesn\'t match, DEFAULT BRANCH HAS LATEST CHANGES THAN ' + branch)
            logEvent('INFO: PLEASE MERGE THE CHANGES FROM DEFAULT BRANCH TO YOUR BRANCH')
            sys.exit(1)
        else:
            cfg = branch_cfg

    return cfg

def replaceSlash(string):
    return os.path.normpath(string)

# We still need this method as wp8 gives us details and we need to copy
# only few files from there.
def copyDirectory(root_src_dir, root_dst_dir):
    logEvent("INFO: Copying from " + root_src_dir + ' to ' + root_dst_dir)
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                try:
                    os.remove(dst_file)
                except:
                    os.system('attrib -R %s' % dst_file)
                    os.remove(dst_file)
            shutil.copy2(src_file, dst_dir)

def removeDir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

def backupResults(src, dst, dev):
    ts = time.strftime('%Y_%m_%d_%H_%M_%S')
    dst = dst + ts + '_' + dev + '/'
    logEvent("INFO: Backing Up Results " + src + ' --> ' + dst)
    try:
        copyDirectory(src, dst)
    except:
        pass

def getSuiteName(fileName):
    fileName = fileName.replace('/', '\\')
    m = re.search('.*\\\(.*)\.xml$', fileName)
    if not m == None:
        suite = m.group(1)
    else:
        m = re.search('.*\\\(.*)$', fileName)
        suite = m.group(1)
    return suite

class Format:
    """ The class to keep the format string to generate the report
        Reads the template file only once for ever.
    """
    fmt = None
    def __init__(self, templateFile):
        if Format.fmt is None:
            try:
                fh = open(templateFile)
                Format.fmt = ''.join(fh.readlines())
                fh.close()
            except:
                traceback.print_exc()

class Executor:
    def __init__(self, testName, platform):
        self.basedir = replaceSlash(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath( __file__ )), '..')))
        self.cfg = get_config(self.basedir)
        logEvent ("INFO: basedir: " + self.basedir)

        self.testName = testName
        self.platform = self.get_platfrom(platform)
        self.template = self.basedir + self.cfg.details.settings.common.template
        self.xmlreport = None

        self.consoldationreport = self.basedir + self.cfg.details.settings[self.platform].consolidationreport
        self.posttestsrcdir = self.basedir + self.cfg.details.settings.common.posttestsrcdir
        self.posttestdstdir = self.basedir + self.cfg.details.settings.common.posttestdstdir
        logEvent("INFO: Actual Platform: [" + platform + '] Short Form: [' + self.platform + ']')

        # Set branch dir name
        dir = self.basedir
        dir = dir.replace("\\", "/")
        #logEvent ("DEBUG: dir: " + dir)
        pattern = re.compile (".*\/(.*)")
        m = pattern.search(dir)
        self.branchDirName = m.group(1)

    def get_platfrom(self, platform_long_name):
        platforms = self.cfg.details.settings.keys()
        for platform in platforms:
            if platform.lower() in platform_long_name.lower():
                return platform
        return None

    def cleanFolderContent(self, path):
        actual_path = replaceSlash(path)
        if os.path.exists(actual_path):
            flag = None
            for root, dirs, files in os.walk(actual_path, topdown=False):
                try:
                    for f in files:
                        flag = "file"
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        flag = "dir"
                        shutil.rmtree(os.path.join(root, d),ignore_errors=True)

                except:
                    logEvent("INFO: Some file was not deleted. Trying to delete that forcefully")
                    if flag == "file":
                        file_to_delete = os.path.join(root, f)
                        os.system('attrib -R %s' %file_to_delete)
                        os.remove(file_to_delete)

    def createTestDirs(self):
        for dir in self.testDirs:
            path = self.basedir + dir.strip()
            if not os.path.exists(path):
                logEvent("INFO: Creating " + path)
                os.makedirs(replaceSlash(path))

    def parse_UnitTest_log(self, log):
        if os.path.getsize(log) == 0:
            logEvent("INFO: " + log + " is empty")
            return -1,-1,-1
        else:
            file = open(log, "r")
            lines = file.readlines()
            file.close()
            line = lines[-1]
            m = re.search("Run:\s([0-9]+)\s+Failure total:\s([0-9]+)\s+Failures:\s([0-9]+)\s+Errors:\s([0-9]+)$",line)
            if not m == None:
                totalCount = int(m.group(1))
                failCount = int(m.group(2))
                passCount = totalCount - failCount
            else:
                m = re.search("OK\s([0-9]+)\stests\spassed$", line)
                if not m == None:
                    passCount = int(m.groups(1)[0])
                    failCount = 0
                    totalCount = passCount + failCount
                else:
                    logEvent("WARNING: " + log + " does not contain test summary")
                    return -1,-1,-1
            return passCount, failCount, totalCount

    def generateReportFile(  self,
                             reportFile,
                             detailTestName,
                             count_passed=0,
                             count_failed=0,
                             count_skipped=0,
                             count_aborted=0,
                             count_total=0,
                             exe_start_time=" ",
                             exe_end_time=" "):
        reportFile = replaceSlash(reportFile)
        logEvent( "INFO: Writing test results to file: " + reportFile )
        report = open(reportFile, "a")
        template = Format(self.template)
        line_to_write = template.fmt % (escape(detailTestName), count_passed, count_failed, count_skipped, count_aborted, count_total) + '\n'
        report.write(line_to_write)
        report.close()

    def parse_UnitTest(self):
        log = self.basedir + self.cfg.details.settings[self.platform][self.testName].log
        log = replaceSlash(log)

        if os.path.exists(log):
            passCount, failCount, totalCount = self.parse_UnitTest_log(log)
            if totalCount == -1:
                logEvent ("WARNING: No Unittest results found")
                return
            reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
            self.generateReportFile(reportFile, self.testName, passCount, failCount, 0, 0, totalCount)
        else:
            logEvent("WARNING: " +  log + ' file is not found' )

    def parseGuidanceTestResult(self, log_file):
        line_count = 0
        field_count = 0
        pass_count = 0
        fail_count = 0
        skip_count = 0
        abort_count = 0

        if not os.path.exists(log_file):
            logEvent( "WARNING: Guidance test result xml file is not found. File name: " + log_file )
            return -1,-1,-1,-1,-1

        if os.path.getsize(log_file) == 0:
            logEvent( "WARNING: Guidance test result xml file is empty. File name: " + log_file )
        else:
            f = open(log_file, 'rb')
            f.readline()
            required_line = f.readline()
            f.close()

            line_count = 0
            field_count = 0
            pass_count = 0
            fail_count = 0
            skip_count = 0
            abort_count = 0

            if re.match("<testsuite errors=", required_line): # Check for the Errors Count.
                required_line = required_line.split(" ")
                fail_count = int(required_line[2].split("=")[1].strip("\""))
                total_count = int(required_line[3].split("=")[1].strip("\""))
            pass_count = total_count - fail_count
        return pass_count, fail_count, skip_count, abort_count, total_count

    def parse_Guidance(self):
        summary_suite = []
        cdtresultsdir = self.basedir + self.cfg.details.settings[self.platform][self.testName].xmlresultdir
        xmllist = glob.glob(cdtresultsdir + '/*.xml')
        for log_file in xmllist:
            try:
                log_file = replaceSlash(log_file.strip())
                #m = re.search('.*/(.*)\.xml$', log_file)
                #suite_name = m.group(1)
                suite_name = getSuiteName(log_file)
                summary_suite.append(suite_name)
                pass_count, fail_count, skip_count, abort_count, total_count = self.parseGuidanceTestResult(log_file)
                if total_count == -1:
                    logEvent ("WARNING: No test result was parsed")
                    return
                detailTestName = self.testName + ' ' + suite_name
                reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
                self.generateReportFile(reportFile, detailTestName, pass_count, fail_count, skip_count, abort_count, total_count)
            except:
                logEvent( "WARNING: Error encountered. Here is the trace back" )
                traceback.print_exc()

        reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
        pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total = self.calculateSummaryCounts(reportFile)
        if total_count_total == -1:
            logEvent ("WARNING: No summary was calculated for routing")
            return
        detailTestName = self.testName + ' ' + ' '.join(summary_suite)
        reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].summaryreport
        self.generateReportFile(reportFile, detailTestName, pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total)

    def parseRoutingTestResult(self, log_file):
        logEvent ("INFO: Parsing route test file: " + str(log_file))
        if (os.path.getsize(log_file) == 0):
            logEvent("WARNING: Routing test result xml file is empty. File name: " + log_file)
            return -1,-1,-1,-1,-1
        else:
            logEvent( "INFO: Parsing routing test result file: " + log_file )
            f = open(log_file, 'rb')
            lines = f.readlines()
            f.close()

            line_count  = 0
            field_count = 0
            pass_count  = 0
            fail_count  = 0
            skip_count  = 0
            abort_count = 0
            total_count = 0
            multi_line  = 0

            for required_line in lines:
                #print "\nDEBUG: line: " + required_line
                if (re.match("<testsuite", required_line) and re.search(">$", required_line)): # Check for the Errors Count.
                    required_line = required_line.strip().strip(">").strip("<").split(" ")
                    #print "\nDEBUG: req_line: " + str(required_line)
                    if (len(required_line) < 7):
                        logEvent ("ERROR: testsuite tag does not contain required information, file: " + log_file)
                        break
                    fail_count = int(required_line[7].split("=")[1].strip("\""))
                    abort_count = int(required_line[6].split("=")[1].strip("\""))
                    total_count = int(required_line[5].split("=")[1].strip("\""))
                    break
                elif(re.match(">", required_line) and multi_line):
                    break
                elif((re.match("<testsuite", required_line) and not re.search(">$", required_line)) or multi_line):
                    required_line = required_line.strip().strip(">").strip("<").strip(" ")
                    multi_line = 1
                    if (re.search ("failures=", required_line)):
                        fail_count = int(required_line.split("=")[1].strip("\""))
                    elif (re.search ("errors=", required_line)):
                        abort_count = int(required_line.split("=")[1].strip("\""))
                    elif (re.search ("tests=", required_line)):
                        total_count = int(required_line.split("=")[1].strip("\""))

            pass_count = total_count - fail_count - abort_count
            #logEvent ("DEBUG: pass " + str(pass_count))
            #if multi_line:
                #logEvent ("DEBUG: Performed multi line match")
        return pass_count, fail_count, skip_count, abort_count, total_count

    def parse_Routing(self):
        summary_suite = []
        cdtresultsdir = self.basedir + self.cfg.details.settings[self.platform][self.testName].csvresultdir
        csvlist = glob.glob(cdtresultsdir + '/*.xml')
        for log_file in csvlist:
            try:
                log_file = replaceSlash(log_file.strip())
                #logEvent ("DEBUG: Checking file: " + log_file)
                if log_file.lower().find('summary') == -1: #parse only suite summaries not binary produced ones.
                    logEvent ("INFO: Processing file: " + log_file)
                    m = re.search('.*\\\(.*)\.xml$', log_file)
                    if m == None:
                        m = re.search('.*/(.*)\.xml$', log_file)
                    if m == None:
                        logEvent ("WARNING: Unable to detect suite_name, results could not be parsed")
                        return
                    suite_name = m.group(1)
                    #logEvent ("DEBUG: suite_name:" + suite_name)
                    summary_suite.append(suite_name)
                    pass_count, fail_count, skip_count, abort_count, total_count = self.parseRoutingTestResult(log_file)
                    if total_count == -1:
                        logEvent ("WARNING: No results were parsed for routing")
                        return

                    detailTestName = self.testName + ' ' + suite_name
                    reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
                    self.generateReportFile(reportFile, detailTestName, pass_count, fail_count, skip_count, abort_count, total_count)
            except:
                traceback.print_exc()

        reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].report
        reportFile = replaceSlash(reportFile)
        pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total = self.calculateSummaryCounts(reportFile)
        if total_count_total == -1:
            logEvent ("\nWARNING: No summary was calculated for routing")
            return
        detailTestName = self.testName + ' ' + ' '.join(summary_suite)
        reportFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].summaryreport
        self.generateReportFile(reportFile, detailTestName, pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total)

    def calculateSummaryCounts(self, reportFile):
        if not os.path.exists(reportFile):
            logEvent ("\nWARNING: Cannot find result file for calculating summary: " + reportFile)
            return -1,-1,-1,-1,-1
        f = open(reportFile, "r")
        detail_log_file_lines = f.readlines()
        f.close()

        pass_count = 0
        fail_count = 0
        skip_count = 0
        abort_count = 0
        total_count = 0

        for line in detail_log_file_lines:
            if re.search("Passed:",line):
                pass_count = pass_count + int(line.split(":")[1].strip())
            elif re.search("Failed:",line):
                fail_count = fail_count + int(line.split(":")[1].strip())
            elif re.search("Skipped:",line):
                skip_count = skip_count + int(line.split(":")[1].strip())
            elif re.search("Aborted:",line):
                abort_count = abort_count + int(line.split(":")[1].strip())

        total_count = pass_count + fail_count + skip_count + abort_count
        return pass_count, fail_count, skip_count, abort_count, total_count

    def generateConsolidationReport(self):

        summarydir = self.summarydir
        reportFile = self.consoldationreport
        summarylogs = glob.glob(summarydir + '/*summary.log')

        #pass_count_total, fail_count_total, skip_count_total, abort_count_total, total_count_total
        sums = [0, 0, 0, 0, 0]
        for summary in summarylogs:
            l = self.calculateSummaryCounts(summary)
            sums = [sum(pair) for pair in zip(sums, l)]
        pass_count, fail_count, skip_count, abort_count, total = sums
        self.generateReportFile(reportFile, 'WHOLE SUMMARY', pass_count, fail_count, skip_count, abort_count, total)

    def convertCsvToXml(self, csvFile, xml):
        if os.path.getsize(csvFile) == 0:
            logEvent( "WARNING: Test result file is empty. File name: " + csvFile )
            return
        else:
            xml_log_file = open(xml, "w")

            f = open(csvFile, 'rb')
            csv_lines = csv.reader(f)

            test_case_count = 0
            fail_count = 0
            field_count = 0
            lines = []

            for row in csv_lines:
                if test_case_count == 0:

                    header = row
                    for field in header:
                        if re.search("suite",field):
                            classname_field_index = field_count
                        elif re.search("case",field):
                            name_field_index = field_count
                        elif re.search("passed",field):
                            passed_field_index = field_count
                        elif re.search("reason",field):
                            reason_field_index = field_count

                        field_count = field_count + 1
                    test_case_count = test_case_count + 1

                else:
                    test_case_count = test_case_count + 1

                    classname = row[classname_field_index]
                    name = row[name_field_index]
                    failure_message = row[reason_field_index]

                    if row[passed_field_index] == "0":
                        fail_count = fail_count + 1
                        lines.append("<testcase classname=\"" + classname + "\" name=\"" + name + "\" >\n")
                        lines.append("<failure message=\"" + failure_message + "\">FAILED</failure>\n")
                        lines.append("</testcase>\n")
                    else:
                        lines.append("<testcase classname=\"" + classname + "\" name=\"" + name + "\" />\n")

            if test_case_count < 1:
                logEvent( "WARNING: No results found in the csv file: " + csv )
                return

            xml_log_file.write("<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n")
            xml_log_file.write("<testsuite errors=\"0\" failures=\"" + str(fail_count)+"\" tests=\"" + str(test_case_count-1) +"\" name=\"Routing\">\n")
            for x in lines:
                xml_log_file.write(x)

            xml_log_file.write("</testsuite>")
            xml_log_file.close()
            f.close()

    def convertToXML(self):
        if self.xmlreport == None:
            return
        logEvent("INFO: " + self.testName.upper() + ' Generating XML files')
        summary_suite = []
        cdtresultsdir = self.basedir + self.cfg.details.settings[self.platform][self.testName].csvresultdir
        xmlresultdir = self.basedir + self.cfg.details.settings[self.platform][self.testName].xmlresultdir
        csvlist = glob.glob(cdtresultsdir + '/*.csv')

        for csv in csvlist:
            csv = replaceSlash(csv.strip())
            if csv.lower().find('summary') == -1: #parse only suite summaries not binary produced ones.
                m = re.search('.*\\\(.*)\.csv$', csv)
                if m == None:
                    m = re.search('.*/(.*)\.csv$', csv)
                suite_name = m.group(1)
                xml = xmlresultdir + '/' + suite_name + '.xml'
                self.convertCsvToXml(csv, xml)

    def convertCppUnitToJUnit(self):
        if self.xmlreport == None:
            return

        xmlOutput = self.basedir + self.cfg.details.settings[self.platform][self.testName].xml_output
        xmlResultDir = self.basedir + self.cfg.details.settings[self.platform][self.testName].xmlresultdir
        xmlFile = self.basedir + self.cfg.details.settings[self.platform][self.testName].xunit_output
        msxslBin = self.basedir + self.cfg.details.settings.common.msxsl
        cppunit2junit_xsl = self.basedir + self.cfg.details.settings.common.cppunit2junit_xsl

        convertCmd = msxslBin + ' ' + xmlOutput + ' ' + cppunit2junit_xsl + ' -o ' + xmlFile

        logEvent("Running: " + convertCmd)
        try:
            retcode = subprocess.call(convertCmd, shell=True)
            if retcode < 0:
                logEvent("[E] Child was terminated by signal " + str(retcode))
                print >>sys.stderr, "[E] Child was terminated by signal ", -retcode
            elif retcode > 0:
                logEvent("[E] XML parsing error " + str(retcode))
            else:
                logEvent("INFO: XML parsed.")
        except OSError, e:
            logEvent("[E] Execution failed: " + str(e))

class Wp8Executor(Executor):
    def __init__(self, testName):
        Executor.__init__(self, testName, os.getenv("PLATFORM"))

        self.testDirs = self.cfg.details.settings[self.platform][self.testName].testdirs
        self.summarydir = self.basedir + self.cfg.details.settings.common.wp8_summarydir

        self.consoldationreport = self.basedir + self.cfg.details.settings[self.platform].consolidationreport

        self.wp8_posttestsrcdir = self.basedir + self.cfg.details.settings.common.wp8_posttestsrcdir
        self.posttestdstdir = self.basedir + self.cfg.details.settings.common.posttestdstdir
        self.createTestDirs()

    def executeCommands(self, cmd, log, timeoutMultiplier):
        global exitCode
        global timeOut
        cmd = cmd
        timeout = self.cfg.details.settings[self.platform][self.testName].timeout
        try:
            if (os.environ["PROCESS_TIMEOUT"] != None):
                timeout = int(os.environ["PROCESS_TIMEOUT"])
        except:
            timeout = timeout

        if (timeout == None or timeout < 0 or timeout == ''):
            timeout = int(3600) # Default timeout of 1 hr

        try:
            timeout = int(timeout)
        except:
            # Timeout value is not an integer value, set default value
            timeout = int(3600) # Default timeout of 1 hr

        # Use timeoutMultiplier to have enough time for all tests to be executed
        if (not timeoutMultiplier>0):
            timeoutMultiplier = 1
        timeout = timeout * timeoutMultiplier
        timeOut = timeout

        self.timeoutExceeded = None
        # Check if timeout exceeded during execution of previous command
        if (self.timeoutExceeded):
            logEvent ("INFO: Timeout period exceeded while executing: " + cmd + ", skipping any remaining commands")
            exitCode = ExitCode.Error
            return 1

        if (log==None):
            log = self.basedir + self.cfg.details.settings[self.platform][self.testName].log
        # Remove leading and trailing spaces
        cmd = cmd.lstrip()
        cmd = cmd.rstrip()
        log = log.lstrip()
        log = log.rstrip()

        cmd = cmd.replace("/", "\\")
        log = log.replace("/", "\\")
        errlog = log + '_err'
        logEvent('INFO: Executing: ' + cmd + ', storing output to log: ' + log)
        logEvent('INFO: Expecting the process to complete in ' + str(timeout) + ' seconds')
        try:
            Fh = open(log, "w")
            ErrFh = open(errlog, "w")
            timer = threading.Timer(timeout, self.procHandler)
            timer.start()
            self.proc = subprocess.Popen(cmd, stdout=Fh, stderr=ErrFh)
            self.proc.wait()
            if (timer.isAlive()):
                timer.cancel()
            if (self.proc.returncode < 0):
                # Raise error as test binary has exited with a negative exit code
                exitCode = ExitCode.Error
                logEvent ("ERROR: Child exited with exit code: " + str(self.proc.returncode))
            else:
                logEvent ("INFO: Child exited with exit code: " + str(self.proc.returncode))

            Fh.close()
            ErrFh.close()
        except Exception as e:
            exitCode = ExitCode.Error
            logEvent ("WARNING: Exception caught while executing: " + str(cmd) + ", excep: " + str(e))

    def procHandler(self):
        global exitCode
        global timeOut
        try:
            exitCode = ExitCode.Error
            self.proc.poll()
            logEvent ("WARNING: Process exceeded timeout[" + str(self.platform) + "-" + str(self.testName) + "][" + str(timeOut) + "], terminating child pid: " + str(self.proc.pid))
            self.proc.kill()
            self.timeoutExceeded = 1
        except Exception as e:
            exitCode = ExitCode.Error
            logEvent ("WARNING: Exception caught while terminating child process: " + str(self.proc.pid))

    def shutDownVM(self):
        logEvent("INFO: Shutting down VM")
        time.sleep(10)
        file = self.basedir + self.cfg.details.settings[self.platform][self.testName].shutdown.filename
        cmds = self.cfg.details.settings[self.platform][self.testName].shutdown.cmds
        f = open(file, 'w')
        f.write('\n'.join(cmds))
        f.close()
        rawcmd = Template(os.getenv("SystemRoot") + self.cfg.details.settings[self.platform][self.testName].shutdown.CMD)
        cmd = rawcmd.substitute(basedir=self.basedir)
        cmd.replace('/', '\\')
        logEvent('INFO: Running Command: ' + cmd)
        os.system(cmd)
        time.sleep(30)
        logEvent("INFO: VM is shutdown")

    def mountVHDHardDisk(self):
        logEvent("INFO: Attaching VHD to local PC")
        file_for_disk_mount = self.basedir + '/test_runner/mount_disk.txt'
        disk_mount_file = open(file_for_disk_mount, "w")
        x = self.cfg.details.settings[self.platform][self.testName].vm_2nd_harddisk
        disk_mount_file.write("SELECT VDISK FILE=\""+ x + "\"\n")
        disk_mount_file.write("ATTACH VDISK")
        disk_mount_file.close()

        mount_bat_file_path = replaceSlash(self.basedir + '/test_runner/mount_vhd.bat')
        logEvent(mount_bat_file_path)
        os.system(mount_bat_file_path)
        time.sleep(20)

    def unmountVHDHardDisk(self):
        logEvent("INFO: Detaching VHD from local PC")
        file_for_disk_unmount = self.basedir + '/test_runner/umount_disk.txt'
        disk_umount_file = open(file_for_disk_unmount, "w")
        x = self.cfg.details.settings[self.platform][self.testName].vm_2nd_harddisk
        disk_umount_file.write("SELECT VDISK FILE=\""+ x +"\"\n")
        disk_umount_file.write("DETACH VDISK")
        disk_umount_file.close()
        unmount_bat_file_path = replaceSlash(self.basedir + '/test_runner/umount_vhd.bat')
        logEvent(unmount_bat_file_path)
        os.system(unmount_bat_file_path)
        time.sleep(20)

    def copy_results(self):
        local_drive_letter = self.cfg.details.settings[self.platform].local_drive_letter
        src = self.cfg.details.settings[self.platform][self.testName].shutdown.srcfolder
        dst = self.basedir + self.cfg.details.settings[self.platform][self.testName].shutdown.dstfolder
        src = src.replace('/', '\\')
        dst = dst.replace('/', '\\')
        logEvent("INFO: Copying Results from VHD to Local Disk")
        copyDirectory(src, dst)
        removeDir(src)

    def gatherResults(self):
        logEvent ("\nINFO: Gathering results")
        self.shutDownVM()
        self.mountVHDHardDisk()
        self.copy_results()
        self.unmountVHDHardDisk()

class Win32Executor(Executor):
    def __init__(self, testName):
        Executor.__init__(self, testName, os.getenv("PLATFORM"))

        self.testName=testName
        self.cmdList = []
        self.datadir= None
        self.exe= None
        self.suites=[]
        self.suites_dir = None
        self.testDirs = self.cfg.details.settings[self.platform][self.testName].testdirs
        self.proc = None # store the sub process
        #self.report = self.cfg.details.settings.win32[self.testName].report
        #The Binaries are creating few summary files which we are not interested in. In order to keep these house keeping
        #files, it is better to launch the binary after changing into this folder. Its clean and safe in our processing.
        self.rawresultsdir = self.basedir + self.cfg.details.settings[self.platform][testName].binresultsdir
        self.summarydir = self.basedir + self.cfg.details.settings.common.summarydir

    def get_suites_from_dir(self, suites_dir):
        logEvent("INFO: Suites Dir: " + suites_dir)
        suites_dir = suites_dir.replace('\\', '\\')
        suites = {}
        for top, dirs, files in os.walk(suites_dir):
            for nm in files:
                if nm.find('.json') != -1 and nm.find('.svn') == -1:
                    top = top.replace('\\', '/')
                    m = re.search('(.*)/\d{8}$', top)
                    if m: # json files can also be outside of testcase directories, ignore them
                        suite = m.group(1)
                        if not suites.has_key(suite):
                            suites[suite] = 1
        return suites.keys()

    def get_suites(self, suite_selector):
        if suite_selector == 'suites_dir':
            raw_suites_dir = Template(self.datadir + self.cfg.dev[self.testName].suites_dir)
            self.suites_dir = raw_suites_dir.substitute(branch=get_branch_name(self.basedir))
            return self.get_suites_from_dir(self.suites_dir)
        elif suite_selector == 'suites':
            return map(lambda suite: self.datadir + self.cfg.dev[self.testName].suites_dir + suite, self.cfg.dev[self.testName].suites)

    def composeCommands(self):
        cmds = self.cfg.details.settings[self.platform][self.testName].CMDLIST
        self.datadir = os.path.split(os.path.split(self.basedir)[0])[0] + '\\' + self.cfg.details.settings.common.datadir
        self.exe = self.cfg.dev[self.testName].win32_exe
        self.suites = self.cfg.dev[self.testName].suites
        for c in cmds:
            c = c.strip()
            rawcmd = Template(c)
            for s in self.suites:
                xm = self.datadir + s.strip()
                suiteName = getSuiteName(xm)
                cmd = rawcmd.substitute(exe=self.exe, basedir=self.basedir, datadir=self.datadir, xml=xm, suite=suiteName)
                self.cmdList.append(cmd)
        return self.cmdList

    def executeCommands(self, cmdLst):
        global exitCode
        global timeOut
        timeout = self.cfg.details.settings[self.platform][self.testName].timeout
        try:
            if (os.environ["PROCESS_TIMEOUT"] != None):
                timeout = int(os.environ["PROCESS_TIMEOUT"])
        except:
            timeout = timeout

        if (timeout == None or timeout < 0 or timeout == ''):
            timeout = int(3600) # Default timeout of 1 hr

        try:
            timeout = int(timeout)
        except:
            # Timeout value is not an integer value, set default value
            timeout = int(3600) # Default timeout of 1 hr

        timeOut = timeout
        self.timeoutExceeded = None
        for cmd in cmdLst:
            # Check if timeout exceeded during execution of previous command
            if (self.timeoutExceeded):
                logEvent ("INFO: Timeout period exceeded while executing: " + cmd + ", skipping any remaining commands")
                exitCode = ExitCode.Error
                return 1
            # Split the command to get the output direction file, since Popen does not support it
            # Replace \ and \\ with / to avoid any issue with regex
            #logEvent('About to invoke: ' + str(cmd))
            cmd = cmd.replace("\\", "/")
            pattern = re.compile(".*\s(.*\>.*)\s")
            log = None
            if (pattern.search(cmd)):
                m = pattern.search(cmd)
                cmdArr = cmd.split(m.group(1))
                # We expect that there is only one '>' in cmd and we get a 2 element array
                cmd = cmdArr[0]
                log = cmdArr[1]
            else:
                # Nothing, no redirection
                cmd = cmd

            # Remove leading and trailing spaces
            cmd = cmd.lstrip()
            cmd = cmd.rstrip()
            log = log.lstrip()
            log = log.rstrip()

            #cmd = cmd.replace("/", "\\")
            #log = log.replace("/", "\\")
            logEvent('INFO: Executing: ' + cmd + ', logging to: ' + log)
            logEvent('INFO: Expecting the process to complete in ' + str(timeout) + ' seconds')
            Fh = None
            try:
                Fh = open(log, "w")
                timer = threading.Timer(timeout, self.procHandler)
                timer.start()
                self.proc = subprocess.Popen(cmd, stdout=Fh, stderr=subprocess.STDOUT)
                self.proc.wait()
                if (timer.isAlive()):
                    timer.cancel()
                if (self.proc.returncode < 0):
                    # Raise error as test binary has exited with a negative exit code
                    exitCode = ExitCode.Error
                    logEvent ("ERROR: Child exited with exit code: " + str(self.proc.returncode))
                else:
                    logEvent ("INFO: Child exited with exit code: " + str(self.proc.returncode))

                Fh.close()
            except Exception as e:
                logEvent ("WARNING: Exception caught while executing: " + str(cmd) + ", excep: " + str(e))
                exitCode = ExitCode.Error
                Fh.close()

    def procHandler(self):
        global exitCode
        global timeOut
        try:
            exitCode = ExitCode.Error
            self.proc.poll()
            logEvent ("ERROR: Process exceeded timeout[" + str(self.platform) + "-" + self.testName + "][" + str(timeOut) + "], terminating child pid: " + str(self.proc.pid))
            self.proc.kill()
            self.timeoutExceeded = 1
        except Exception as e:
            exitCode = ExitCode.Error
            logEvent ("WARNING: Exception caught while terminating child process: " + str(self.proc.pid))

def timeFmt():
    return time.strftime('%d:%m:%Y %H:%M:%S')

def logEvent(text):
    print "\n[%s]\t%s" % (timeFmt(), text)

def escape(text):
    return "\'" + text + "\'"

print __name__

if __name__ == "__main__":
    logEvent("[exec]" + " ".join(sys.argv))

    import pdb
    pdb.set_trace()


    # print environment variables
    for e in ["PLATFORM","STEP","TEST_SET"]:
        logEvent("[environment] " + e + "=" + str(os.getenv(e)))

    if sys.platform.lower().startswith('win'):
        os.system("regedit /s disable_crash_popup.reg")

    platform = os.getenv("PLATFORM")
    basedir = replaceSlash(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath( __file__ )), '..')))

    cfg = get_config(basedir)

    tests = cfg.dev.tests
    logEvent("[config] Tests: " + str(tests))
    vmadress = None

    # check if test set is defined as env variable
    if os.getenv("TEST_SET") != None and len(os.getenv("TEST_SET")) > 0 :
        test_set = os.getenv("TEST_SET").split(',')
        if len(test_set) > 0 :
            tests = list(set(tests) & set(test_set))
            logEvent("[env] Tests: " + str(tests))

    # parse command arguments
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, '', ['tests=', 'vmaddress='])

        for o, a in opts:
            # overwrite tests from command line
            if o == "--tests":
                tests = a.split(',')
                logEvent("[argv] Tests: " + str(tests))
            if o == "--vmaddress":
                vmadress = a.split(',')[0]
                logEvent("[argv] vmaddress: " + str(vmadress))

    except:
        logEvent("[E] Error parsing arguments")
        traceback.print_exc()

    if(len(tests)):
        logEvent("Tests to be executed: " + str(tests))
    else:
            logEvent("[E] Test set is empty ")
            exitCode = ExitCode.Skipped

    suite = []

    if platform.lower().startswith('win'):

        for test in tests:
            if   test == 'unittest':
                suite.append(Win32Unit())
            elif test == 'guidance':
                suite.append(Win32Guidance())
            elif test == 'routing':
                suite.append(Win32Routing())
            elif test == 'rendering_rt':
                suite.append(Win32Rendering_RT())
            elif test == 'rendering_perf':
                suite.append(Win32Rendering_Perf())
            elif test == 'traffic':
                suite.append(Win32Traffic())
            else:
                logEvent("[E] Unknown win32 test: " + test)
                exitCode = ExitCode.Skipped

        for test in suite:
            test.run()

        for test in suite:
            test.parse()
            test.convertToXML()

        if (len(suite)):
            test = suite[-1]
            test.generateConsolidationReport()
            backupResults(test.posttestsrcdir, test.posttestdstdir, platform)

    elif platform.lower().startswith('wp8_arm'):
        # Remove test dir
        if os.path.exists(basedir + cfg.details.settings.common.posttestsrcdir):
            logEvent ("INFO: Removing existing result dir: " + basedir + cfg.details.settings.common.posttestsrcdir)
            try:
                shutil.rmtree(basedir + cfg.details.settings.common.posttestsrcdir)
            except Exception as e:
                logEvent ("WARNING: Unable to remove old results dir: " + basedir + cfg.details.settings.common.posttestsrcdir)

        for test in tests:
            if 'nwwptest' in test:
                logEvent ("INFO: nwwptest tests are selected to be executed")
                suite.append(Wp8DeviceNwWpTest(test))
            elif 'unittest' in test:
                logEvent ("INFO: nwwptest unittest is selected to be executed")
                suite.append(Wp8DeviceUnitTest(test))
            elif 'guidance' in test:
                logEvent ("INFO: nwwptest guidance is selected to be executed")
                suite.append(Wp8DeviceNwWpTest(test))
            elif 'routing' in test:
                logEvent ("INFO: nwwptest guidance is selected to be executed")
                suite.append(Wp8DeviceNwWpTest(test))
            else:
                logEvent("[E] Unknown wp8_arm test: " + test)
                exitCode = ExitCode.Skipped

        for test in suite:
            logEvent ("INFO: Executing " + test.getName())
            test.run()
        for test in suite:
            test.parse()
            test.convertToXML()

        if (len(suite)):
            test = suite[-1]
            logEvent ("INFO: Archiving results:")
            backupResults(test.wp8_posttestsrcdir, test.posttestdstdir, platform)

    elif platform.lower().startswith('wp8_x86'):
        # Remove test dir
        if os.path.exists(basedir + cfg.details.settings.common.wp8_posttestsrcdir):
            logEvent ("INFO: Removing existing result dir: " + basedir + cfg.details.settings.common.wp8_posttestsrcdir)
            try:
                shutil.rmtree(basedir + cfg.details.settings.common.wp8_posttestsrcdir)
            except Exception as e:
                logEvent ("WARNING: Unable to remove old results dir: " + basedir + cfg.details.settings.common.wp8_posttestsrcdir)

        for test in tests:
            if   test == 'unittest':
                logEvent ("INFO: unit tests are selected to be executed")
                suite.append(Wp8Unit())
            elif test == 'guidance':
                logEvent ("INFO: guidance tests are selected to be executed")
                suite.append(Wp8Guidance())
            elif test == 'routing':
                logEvent ("INFO: routing tests are selected to be executed")
                suite.append(Wp8Routing())
            elif test == 'traffic':
                logEvent ("INFO: traffic tests are selected to be executed")
                suite.append(Wp8Traffic(vmadress))
            else:
                logEvent("[E] Unknown wp8 test: " + test)
                exitCode = ExitCode.Skipped
            # Temporarily disabling rendering tests for WP8
            """elif test == 'rendering_perf':
                logEvent ("INFO: rendering_perf tests are selected to be executed")
                suite.append(Wp8Rendering_Perf())
            elif test == 'rendering_rt':
                logEvent ("INFO: rendering_rt tests are selected to be executed")
                suite.append(Wp8Rendering_Rt())"""

        for test in suite:
            logEvent ("INFO: Executing " + test.getName())
            test.run()

        if (len(suite)):
            logEvent ("INFO: Gathering results from VHD")
            test = suite[-1]
            test.gatherResults()

        for test in suite:
            logEvent ("INFO: Parsing results for " + test.getName())
            test.parse()
            test.convertToXML()

        if (len(suite)):
            logEvent ("INFO: Parsing results")
            test = suite[-1]
            #test.gatherResults()
            logEvent ("INFO: Generating consolidated report")
            test.generateConsolidationReport()
            logEvent ("INFO: Archiving results:")
            backupResults(test.wp8_posttestsrcdir, test.posttestdstdir, platform)

logEvent ("INFO: Exiting with exitcode: " + str(exitCode))
exit(int(exitCode))