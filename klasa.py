import pyaudio
import numpy
import scipy
import time
import aubio
from music21 import chord

class APU:

    import pyaudio
    import numpy
    import scipy
    import scipy.signal

    MONO=1
    BUTTERWORTH_ORDER=5
    DEFAULT_SAMPLE_SIZE=4096

    __pyaud=None
    stream=None
    mic_index=None

    sample_size=4096
    frequency=0.0
    sampling_rate=48000

    NOTE_NAMES = 'C C# D D# E F F# G G# A A# B'.split()

    last_notes = []
    to_chords = []
    counter = 0



    high_pass=4
    low_pass=10000
    def freq_to_number(self, f): return 69 + 12*numpy.log2(f/440.0)
    def number_to_freq(self, n): return 440 * 2.0**((n-69)/12.0)
    def note_name(self, n): return self.NOTE_NAMES[round(n) % 12]

    def __init__(self): #wait for the user to pick microphone and start recording before initializing everything.
        self.__pyaud=pyaudio.PyAudio()
        self.sample_size=self.DEFAULT_SAMPLE_SIZE
        #TODO: complain if there's no input device

    def getPyAudio(self):
        return(self.__pyaud)

    def getStream(self):
        return(self.stream)


    def getMicrophoneList(self):
        retval={}
        adict=None
        for devindex in range(self.getPyAudio().get_device_count()):
            adict=self.getPyAudio().get_device_info_by_index(devindex)
            if(bool(int(adict["maxInputChannels"]))):
                retval[adict["name"]]=adict["index"]
        return(retval)

    def setMicrophone(self,index):
        self.mic_index=index
        if(self.stream):
            self.stop()

    def getSampleSize(self):
        return(self.sample_size)

    def getFrequency(self):
        return(self.frequency)

    def getSamplingRate(self):
        return(self.sampling_rate)

    def setSampleSize(self, size):
        self.sample_size=size
        self.start()

    def setSamplingRate(self, rate):
        self.sampling_rate=rate
        self.start()

    def setHighPass(self, freq):
        self.high_pass=freq

    def setLowPass(self, freq):
        self.low_pass=freq

    def calcFrequency(self):
        if(self.stream):
            readbuf=self.stream.read(self.sample_size, exception_on_overflow=False)
            data=numpy.fromstring(readbuf, dtype=numpy.float32)

            tolerance = 0.2
            win_s = 4096 # fft size
            hop_s = self.sample_size # hop size
            pitch_o = aubio.pitch("default", win_s, hop_s, self.sampling_rate)
            pitch_o.set_unit("Hz")
            pitch_o.set_tolerance(tolerance)
            pitch = pitch_o(data)[0] #Wynik pojawia się w jednoelementowej liście
            self.frequency=pitch


    def start(self):
        if(self.stream):
            self.stop()
        if(not self.mic_index):
            self.mic_index=int(self.getPyAudio().get_default_input_device_info()["index"])
            self.setSamplingRate(int(self.getPyAudio().get_device_info_by_index(self.mic_index)["defaultSampleRate"]))
        self.stream=self.getPyAudio().open(format=pyaudio.paFloat32,channels=self.MONO,input_device_index=self.mic_index,rate=self.sampling_rate,input=True, frames_per_buffer=self.sample_size)

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()

    def implode(self):
        self.stop()
        self.getPyAudio().terminate()

    def toggle(self):
        if(self.stream):
            self.stop()
        else:
            self.start()

    def test(self):
        self.calcFrequency()
        freq = self.getFrequency()
        number = self.freq_to_number(freq)
        if freq > 0:
            note = self.note_name(number)
        if freq==0:
            self.counter+=1
            if self.counter>30:
                self.counter = 0
                self.to_chords = []
                self.last_notes = []
        else:
            if len(self.last_notes) >= 2:
                if self.last_notes[len(self.last_notes)-1]==self.last_notes[len(self.last_notes)-2]==note:
                    if note not in self.to_chords:
                        self.to_chords.append(note)
                        self.counter = 0
            self.last_notes.append(note)
        if(len(chord.Chord(self.to_chords).pitchedCommonName) > 5 and len(self.to_chords) >2 and self.counter > 20):
            self.counter = 41
            return [chord.Chord(self.to_chords).pitchedCommonName]
        if(freq > 50):
            nearest_note_number = round(number)
            nearest_note_freq = self.number_to_freq(nearest_note_number)
            freq_difference = nearest_note_freq - freq
            return [freq, note, nearest_note_freq, freq_difference]
        return [freq]



