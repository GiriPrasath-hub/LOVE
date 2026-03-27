import speech_recognition as sr

recognizer = sr.Recognizer()

def listen():

    try:
        with sr.Microphone() as source:

            print("LOVE listening...")

            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            audio = recognizer.listen(source, phrase_time_limit=5)

        command = recognizer.recognize_google(audio)

        print("You:", command)

        return command.lower()

    except:
        return ""