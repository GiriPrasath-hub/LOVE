import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

MODEL_PATH = "models/vosk-model-small-en-us-0.15"

class VoskListener:

    def __init__(self):
        self.model = Model(MODEL_PATH)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.q = queue.Queue()

    def _callback(self, indata, frames, time, status):
        self.q.put(bytes(indata))

    def listen(self):

        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._callback,
        ):

            while True:
                data = self.q.get()

                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    text = result.get("text", "")
                    return text.lower()