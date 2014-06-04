import math
import wave
import struct

def composeNotes(freq=[440],coef=[1], datasize=10000, fname="test.wav"):
    frate = 44100.00
    amp=8000.0
    sine_list=[]
    for x in range(datasize):
        samp = 0
        for k in range(len(freq)):
            samp = samp + coef[k] * math.sin(2*math.pi*freq[k]*(x/frate))
        sine_list.append(samp)
    wav_file=wave.open(fname,"w")
    nchannels = 1
    sampwidth = 2
    framerate = int(frate)
    nframes=datasize
    comptype= "NONE"
    compname= "not compressed"
    wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
    for s in sine_list:
        wav_file.writeframes(struct.pack('h', int(s*amp/2)))
    wav_file.close()

def writeToFile(fname, datasize, sine_list):
    wav_file=wave.open(fname,"w")
    nchannels = 1
    sampwidth = 2
    framerate = int(44100.00)
    nframes=datasize
    comptype= "NONE"
    compname= "not compressed"
    wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
    for s in sine_list:
        wav_file.writeframes(struct.pack('h', int(s*8000.0/2)))
    wav_file.close()

def composeNotesInSequence(freq, coef, datasize=10000, sine_list=[]):
    for x in range(datasize):
        samp = coef * math.sin(2*math.pi*freq*(x/44100.00))
        sine_list.append(samp)

middleKeys = {
              'C4': 261.63,
              #'Cf4' : 277.18,
              'D4' : 293.66,
              #'Df4' : 311.13,
              'E4' : 329.63,
              'F4' : 349.23,
              #'Ff4' : 369.99,
              'G4' : 392.00,
              #'Gf4' : 415.30,
              'A4' : 440.00,
              #'Af4' : 466.16,
              'B4' : 493.88,
              'C5': 523.25
              }
"""
    for key in middleKeys.keys():
        composeNotes([middleKeys[key]], [0.1], 20000, "C:\\notes\\" + key + ".wav")

    waveList = []
    composeNotesInSequence(261.63, 1.0, 20000, waveList)
    composeNotesInSequence(293.66, 1.0, 20000, waveList)
    composeNotesInSequence(329.63, 1.0, 20000, waveList)
    composeNotesInSequence(349.23, 1.0, 20000, waveList)
    composeNotesInSequence(392.00, 1.0, 20000, waveList)
    composeNotesInSequence(440.00, 1.0, 20000, waveList)
    composeNotesInSequence(493.88, 1.0, 20000, waveList)
    composeNotesInSequence(523.25, 1.0, 20000, waveList)

    writeToFile("C:\\notes\\notes.wav", 20000, waveList)
"""

#Compose Song with the Notes !!!
frequencies = {
      'C' : 261.63,
      'D' : 293.66,
      'E' : 329.63,
      'F' : 349.23,
      'G' : 392.00,
      'A' : 440.00,
      'B' : 493.88,
      ' ' : 0.0
}

song = "CCGGAAG FFEEDDC GGFFEED GGFFEED CCGGAAG FFEEDDC "
songWave = []
for note in song:
    composeNotesInSequence(frequencies[note], 1.0, 15000, songWave)

writeToFile("C:\\notes\\twinkleN.wav", 15000, songWave)
