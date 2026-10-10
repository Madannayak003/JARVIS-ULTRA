import speech_recognition as sr

recognizer = sr.Recognizer()


def listen():

    with sr.Microphone() as source:

        recognizer = sr.Recognizer()

        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        recognizer.pause_threshold = 2.0
        recognizer.phrase_threshold = 0.5
        recognizer.non_speaking_duration = 1.0

        print("Listening...")

        audio = recognizer.listen(

            source,

            timeout=None,

            phrase_time_limit=30

        )

    try:

        query = recognizer.recognize_google(audio)

        print("You :", query)

        return query.lower()

    except:

        return ""