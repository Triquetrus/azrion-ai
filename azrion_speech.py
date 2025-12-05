import os
os.environ["VOSK_LOG_LEVEL"] = "0"

import sys
import queue
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from azrion import azrion_chat,say,get_ai_greeting

def main():
    # Same greeting as text client
    print("Hey Triquetrus!")
    greeting = get_ai_greeting()
    print(greeting)
    # Speak both lines
    say("Hey Triquetrus!")
    say(greeting)

    print("\nAzrion voice is listening. Say something; Ctrl+C to stop.\n")

    # Load Vosk model ...
    model = Model("models/en_us_small")

    samplerate = 16000  # Hz
    device = None       # default input device
    q = queue.Queue()

    def callback(indata, frames, time_, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=samplerate,
                           blocksize=8000,
                           dtype="int16",
                           channels=1,
                           callback=callback,
                           device=device):
        rec = KaldiRecognizer(model, samplerate)

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                try:
                    text = json.loads(result).get("text", "").strip()
                except Exception:
                    text = ""

                if text:
                    print(f"🎙 Heard: {text}")
                    lower = text.lower()

                    # Voice-level exit keywords
                    if lower in ["exit", "by" ,"bye", "goodbye", "quit"]:
                        reply = "Bye! Talk to you later."
                        print(f"Azrion: {reply}")
                        say(reply)
                        break  # leave the while loop

                    reply = azrion_chat(text)
                    print(f"Azrion: {reply}")
                    say(reply)
            else:
                # ignore partials for now
                pass

print("Azrion voice: session ended.") 

if __name__ == "__main__":
    main()
