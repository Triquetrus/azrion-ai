import time
from azrion import azrion_chat, get_ai_greeting

def main():
    print("Azrion (voice client skeleton)")
    print(get_ai_greeting())
    print("Type here for now; we'll hook mic input later.\n")

    while True:
        user_input = input("🎙 (simulated voice) >>> ").strip()

        if user_input.lower() in ["exit", "bye"]:
            print("Azrion: Bye! Voice mode off 😉")
            break

        reply = azrion_chat(user_input)
        time.sleep(0.15)

if __name__ == "__main__":
    main()
