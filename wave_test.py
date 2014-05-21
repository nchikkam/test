import numpy as N
import wave
import unittest

class TestWave(unittest.TestCase):

    def test_sineWave(self):

        fileName = "a.wav"

        # parameters needed for the wav file
        nchannels = 1
        sampwidth = 2
        duration  = 2 # seconds
        framerate = 44100 # Hz
        nframes   = duration * framerate
        comptype  = 'NONE'  # ALL CAPS!!! Compression Type
        compname  = 'not compressed'

        # sine wave generation
        frequency = 440 # Hz
        period = framerate / float(frequency) # in sample points
        omega = N.pi * 2 / period

        xaxis = N.arange(int(period),dtype = N.float) * omega
        ydata = 16384 * N.sin(xaxis)

        signal = N.resize(ydata, (nframes,))
        print signal

        ssignal = ''
        for i in range(len(signal)):
           ssignal += wave.struct.pack('h',signal[i]) # transform to binary

        file = wave.open(fileName, 'wb')

        #wave.setparams(nchannels, sampwidth, framerate, nframes, comptype, compname)
        file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname)) # channels set to 1, which means there won't be stereo in the wav
        file.writeframes(ssignal)
        file.close()

        f = wave.open(fileName, 'rb')
        self.assertEqual(nchannels, f.getnchannels())
        self.assertEqual(sampwidth, f.getsampwidth())
        self.assertEqual(framerate, f.getframerate())
        self.assertEqual(nframes,   f.getnframes())
        self.assertEqual(comptype,  f.getcomptype())
        self.assertEqual(compname,  f.getcompname())
        self.assertEqual(ssignal,   f.readframes(f.getnframes()))
        f.close()

if __name__ == '__main__':
    unittest.main()
    
