import numpy as N
import wave

def make_copy(fileName):

    ifile = wave.open(fileName)
    ofile = wave.open("output.wav", "w")
    ofile.setparams(ifile.getparams())

    sampwidth = ifile.getsampwidth()
    fmts = (None, "=B", "=h", None, "=l")
    fmt = fmts[sampwidth]
    dcs  = (None, 128, 0, None, 0)
    dc = dcs[sampwidth]

    for i in range(ifile.getnframes()):
        iframe = ifile.readframes(1)

        iframe = wave.struct.unpack(fmt, iframe)[0]
        iframe -= dc

        oframe = iframe / 2;

        oframe += dc
        oframe = wave.struct.pack(fmt, oframe)
        ofile.writeframes(oframe)

    ifile.close()
    ofile.close()


def create_sineWave(fileName):
    # Prepare signal
    duration = 4 # seconds
    samplerate = 44100 # Hz
    samples = duration*samplerate
    frequency = 440 # Hz
    period = samplerate / float(frequency) # in sample points
    omega = N.pi * 2 / period

    xaxis = N.arange(int(period),dtype = N.float) * omega
    ydata = 16384 * N.sin(xaxis)

    signal = N.resize(ydata, (samples,))

    ssignal = ''
    for i in range(len(signal)):
       ssignal += wave.struct.pack('h',signal[i]) # transform to binary

    file = wave.open(fileName, 'wb')
    noOfChannels = 1
    file.setparams((noOfChannels, 2, samplerate, 44100*4, 'NONE', 'noncompressed')) # channels set to 1, which means there won't be stereo in the wav
    file.writeframes(ssignal)
    file.close()

    print 'file written'
    make_copy(fileName)


def make_reverse(fileName):

    ifile = wave.open(fileName)
    ofile = wave.open("reverse.wav", "w")
    ofile.setparams(ifile.getparams())

    sampwidth = ifile.getsampwidth()
    fmts = (None, "=B", "=h", None, "=l")
    fmt = fmts[sampwidth]
    dcs  = (None, 128, 0, None, 0)
    dc = dcs[sampwidth]

    for i in range(ifile.getnframes(), 0, -1):
        iframe = ifile.readframes(1)

        iframe = wave.struct.unpack(fmt, iframe)[0]

        print iframe

        iframe -= dc

        oframe = iframe # / 2;

        oframe += dc
        oframe = wave.struct.pack(fmt, oframe)
        ofile.writeframes(oframe)

    ifile.close()
    ofile.close()

make_reverse('cde.wav')


