import pyttsx3
from config.settings import VOICE_RATE

engine = pyttsx3.init()
engine.setProperty("rate", VOICE_RATE)

def speak(text):
    print("LOVE:", text)
    engine.say(text)
    engine.runAndWait()