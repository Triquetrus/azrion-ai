from azrion import (
    get_ai_greeting,
    add_task,
    complete_task,
    search_full_history,
    azrion_chat,
)
import time

# --- MAIN LOOP ---
def main():
    print("Hey Triquetrus!")
    print(get_ai_greeting())
    while True:
        user_input = input(">>> ").strip()

        # --- TASK COMMANDS ---
        if user_input.lower().startswith("add task "):
            task_desc = user_input[9:]
            add_task(task_desc)
            print("Azrion: Got it! Task added 😉")
            continue
        elif user_input.lower().startswith("done "):
            task_desc = user_input[5:]
            complete_task(task_desc)
            print("Azrion: Nice! Task marked as done 😏")
            continue

        # on-demand search command
        if user_input.lower().startswith("search history:"):
            # azrion_chat already handles this, but allow direct call to show results
            results = search_full_history(user_input.split(":",1)[1])
            if not results:
                print("Azrion: No matches found in history.")
            else:
                print("Azrion: Found these matches:")
                for r in results[:8]:
                    print(" -", r)
            continue

        if user_input.lower() in ["exit", "bye"]:
            print("Azrion: Bye! Talk to you later 😉")
            break

        # normal chat
        reply = azrion_chat(user_input)
        # azrion_chat already typed out the reply; still print indicator if needed
        time.sleep(0.15)

if __name__ == "__main__":
    main()
