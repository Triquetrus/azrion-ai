import sys
import queue
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from azrion import azrion_chat,say

def main():
    print("Azrion voice: mic test (speech -> text)")
    print("Say something; Ctrl+C to stop.\n")

    # Load Vosk model (relative path from project root)
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
                     reply = azrion_chat(text)
                     print(f"Azrion: {reply}")
                     say(reply)

            else:
                # Optional: handle partial results if you want
                pass

if __name__ == "__main__":
    main()
