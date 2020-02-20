import speech_recognition as sr
import matplotlib.pyplot as plt
import numpy as np
import wave
import sys


def main():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print("Please say something")
        audio = r.listen(source)
        print("Recognizing Now .... ")
        # recognize speech using google
        try:
            r.recognize_bing()
            print("You have said \n" + r.recognize_google(audio, language='he'))
            print("Audio Recorded Successfully \n ")
        except Exception as e:
            print("Error :  " + str(e))
        # write audio
        with open("recorded.wav", "wb") as f:
            f.write(audio.get_wav_data())

    spf = wave.open("recorded.wav", "r")

    # Extract Raw Audio from Wav File
    signal = spf.readframes(-1)
    signal = np.fromstring(signal, "Int16")

    # If Stereo
    if spf.getnchannels() == 2:
        print("Just mono files")
        sys.exit(0)

    plt.figure(1)
    plt.title("Signal Wave...")
    plt.plot(signal)
    plt.show()


if __name__ == "__main__":
    main()

