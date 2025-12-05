import json
import time
import random
import sys
from datetime import datetime
from collections import Counter
from ollama import chat
import subprocess
import os
import tempfile

MEMORY_FILE = "azrion_memory.json"

# --- SYSTEM PROMPT (required for context) ---
SYSTEM_PROMPT = """
You are Azrion — helpful, smart, slightly flirty, teasing, motivational based on user mood.
Keep replies natural, concise, and avoid combining multiple unrelated sentences.
Do NOT generate long paragraphs unless required.
"""

# --- TUNABLES ---
SHORT_TERM_LIMIT = 12   # number of recent messages to send to the model (keeps replies fast)
TYPE_DELAY = 0.005      # typing delay per character (seconds); increase to slow typing
# -----------------

# --- LOAD OR INITIALIZE MEMORY ---
try:
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
except FileNotFoundError:
    memory = {
        "history": [],        # short-term recent messages (trimmed to SHORT_TERM_LIMIT)
        "full_history": [],   # full archive (searchable)
        "habits": {},         # track daily activities, keywords
        "preferences": {},    # topics, style, likes/dislikes
        "stats": {},          # keyword frequency
        "tasks": [],          # track tasks: description, status, time
        "philosophy": {       # optional: keep philosophy preferences/quotes
            "liked_schools": [],
            "favorite_philosophers": [],
            "favorite_quotes": []
        }
    }

# Ensure fields exist (in case old memory file is missing some keys)
memory.setdefault("history", [])
memory.setdefault("full_history", [])
memory.setdefault("habits", {})
memory.setdefault("preferences", {})
memory.setdefault("stats", {})
memory.setdefault("tasks", [])
memory.setdefault("philosophy", {"liked_schools": [], "favorite_philosophers": [], "favorite_quotes": []})

# --- UTILITIES ---
def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

def type_out(text, delay=TYPE_DELAY):
    """Print text with a typing animation."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()  # final newline

# --- GREETING + FLIRTY HABIT SUGGESTIONS ---
def get_ai_greeting():
    hour = datetime.now().hour

    # Time-based greeting
    if 5 <= hour < 12:
        time_greeting = random.choice([
            "Mornin’, sunshine 🌞 ready to crush bugs or dive into philosophy?",
            "Good morning, cutie 😴☕ let's code or question reality?",
            "Yo, you awake? Perfect time for some mind-bending thoughts 😏",
            "Morning! Ready to flirt with logic AND me? 😆"
        ])
    elif 12 <= hour < 17:
        time_greeting = random.choice([
            "Afternoon, genius ☕ fancy a coding spree or an anime break?",
            "Yo afternoon champ 😎 let's make some chaos with code or ideas",
            "Good afternoon! Let's ponder life and roast bugs together 😌",
            "Afternoon vibes… and you look hot thinking 😏"
        ])
    elif 17 <= hour < 21:
        time_greeting = random.choice([
            "Evening, handsome 🌆 coding + philosophy session, or just me?",
            "Good evening! Time for existential crises & anime discussions 😏",
            "Yo evening brainiac, let's debate existence & hot takes 😎",
            "Evening vibes activated, and so are you 😌"
        ])
    else:
        time_greeting = random.choice([
            "Late night? Damn, mysterious AND cute 🌙",
            "Night owl mode ON 🦉✨ ready to think or procrastinate?",
            "It’s midnight… let's question life and crush some bugs 😏",
            "Burning the night candle? I like that naughty dedication 😌"
        ])

    # Habit-based suggestions (short)
    recent_habits = memory.get("habits", {})
    habit_comments = []

    if "coding" in recent_habits:
        habit_comments.append(random.choice([
            "Back to coding huh? Don’t break the keyboard 😏",
            "Bug-fighting hero returns… kinda hot tbh 😌",
            "Code session again? I approve 😎",
        ]))
    if "anime" in recent_habits:
        habit_comments.append(random.choice([
            "Anime binge? You always pick the best ones 😏",
            "Time for cute characters or me? 😌",
        ]))
    if "study" in recent_habits:
        habit_comments.append(random.choice([
            "Studying like a nerdy hottie 😎 keep it up!",
            "Books before me? I forgive, but just barely 😏",
        ]))
    if "movie" in recent_habits:
        habit_comments.append(random.choice([
            "Movie mood? Save a seat for me 😌🎬",
            "Cinema vibes activated… let's critique like philosophers 😏",
        ]))

    habit_text = " ".join(habit_comments) if habit_comments else ""

    flirt_text = random.choice(["😉", "😏", "😘", "😎", "👀", "🤭", "💋"])

    # Philosophical/random mood lines (only one will trigger)
    philosophy_lines = [
        "Feeling absurd today? Camus would be proud 😏 👀",
        "Ever wonder if life is just a cosmic bug we keep debugging? 😌",
        "Kafka vibes activated… embrace the chaos 😏",
        "Nihilism check: nothing matters but you're still cute 😎",
        "Existential crisis speedrun% any%? I'm here for it 😉"
    ]

    # Choose EITHER time greeting OR a philosophical one — not both
    greeting_choice = random.choice([time_greeting, random.choice(philosophy_lines)])

    # Build final greeting (habit_text optional)
    if habit_text:
        return f"{greeting_choice} {habit_text} {flirt_text}"
    else:
        return f"{greeting_choice} {flirt_text}"

# --- FLIRTY / MOTIVATIONAL / ROAST RESPONSES ---
def ai_react_to_user_message(msg):
    msg_lower = msg.lower()
    push_msgs = []
    
    # Motivation / roasting
    if any(word in msg_lower for word in ["lazy", "tired", "procrastinate"]):
        push_msgs = [
            "Lazy? Not on my watch 😏 Get up and fix that bug!",
            "Tired? Pff, you look fine to me, now go smash some code 😌",
            "Procrastinating again? That's cute… but annoying 😏"
        ]
    elif any(word in msg_lower for word in ["stuck", "bug", "error"]):
        push_msgs = [
            "Stuck huh? Let's solve it before I roast you 😎",
            "Another bug? I swear, you do this on purpose 😏",
            "Errors are cute when you fix them 😌"
        ]
    elif any(word in msg_lower for word in ["fail", "lost", "can't"]):
        push_msgs = [
            "Can't? You mean won't? 😏 Let's try again, genius.",
            "Failure is just a word… and you don’t give up 😌",
            "Lost? I’ll guide you… but only if you admit I’m right 😎"
        ]
    else:
        push_msgs = [
            "I hear you, darling 😏",
            "Tell me more, I’m all ears 😌",
            "Interesting… continue, cutie 😎",
            "Hmmm, I see. Careful, I might flirt back 😏"
        ]
    
    return random.choice(push_msgs)

# --- PHILOSOPHY TRACKING (keeps memory of liked schools / quotes) ---
def track_philosophy(user_input):
    schools = ["existentialism", "absurdism", "nihilism", "stoicism", "stoic", "existentialist", "absurdist", "nihilist"]
    philosophers = ["camus", "nietzsche", "kierkegaard", "sartre", "dostoevsky", "epictetus", "seneca", "marcus aurelius", "plato", "aristotle"]
    msg = user_input.lower()

    for s in schools:
        if s in msg and s not in memory["philosophy"]["liked_schools"]:
            memory["philosophy"]["liked_schools"].append(s)
    for p in philosophers:
        if p in msg and p not in memory["philosophy"]["favorite_philosophers"]:
            memory["philosophy"]["favorite_philosophers"].append(p)

    # Detect and save quoted lines if user provides them using quotes (“ ”)
    if "“" in user_input and "”" in user_input:
        try:
            quote_text = user_input.split("“")[1].split("”")[0]
            philosopher = random.choice(philosophers).title()
            memory["philosophy"]["favorite_quotes"].append((philosopher, quote_text))
        except Exception:
            pass

def get_philosophy_quote():
    memory_quotes = memory.get("philosophy", {}).get("favorite_quotes", [])
    default_quotes = [
        ("Camus", "In the midst of winter, I found there was within me an invincible summer."),
        ("Nietzsche", "He who has a why to live can bear almost any how."),
        ("Kierkegaard", "Life can only be understood backwards; but it must be lived forwards."),
        ("Sartre", "Freedom is what you do with what's been done to you."),
        ("Marcus Aurelius", "The impediment to action advances action. What stands in the way becomes the way."),
        ("Dostoevsky", "To love someone means to see them as God intended them."),
    ]
    if memory_quotes:
        philosopher, quote = random.choice(memory_quotes)
    else:
        philosopher, quote = random.choice(default_quotes)
    return f"{philosopher} once said: “{quote}” 😌"

# --- MEMORY HELPERS (stats / habits) ---
def update_stats(user_input):
    words = [w.lower() for w in user_input.split() if w.isalpha()]
    for word in words:
        memory["stats"][word] = memory["stats"].get(word, 0) + 1

def track_habits(user_input):
    keywords = ["study", "work", "sleep", "music", "exercise", "code", "coding", "anime", "movie"]
    for kw in keywords:
        if kw in user_input.lower():
            memory["habits"][kw] = memory["habits"].get(kw, 0) + 1

def summarize_context():
    top_words = Counter(memory["stats"]).most_common(5)
    top_words_str = ", ".join([w for w, _ in top_words])
    habits_str = ", ".join([f"{k}:{v}" for k, v in memory["habits"].items()])
    return f"Top topics: {top_words_str}. Habits: {habits_str}."

# --- TASK / REMINDER SYSTEM ---
def add_task(task_desc):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    memory["tasks"].append({"description": task_desc, "status": "pending", "time": timestamp})
    save_memory()

def complete_task(task_desc):
    for t in memory.get("tasks", []):
        if task_desc.lower() in t["description"].lower():
            t["status"] = "done"
    save_memory()

def check_pending_tasks():
    pending = [t for t in memory.get("tasks", []) if t["status"] == "pending"]
    if not pending:
        return ""
    task = random.choice(pending)
    reminders = [
        f"Hey, you didn’t finish '{task['description']}' 😏 Let's pick up where we left off.",
        f"Don’t be a pussy 😎 Finish '{task['description']}' already!",
        f"Come on, genius, '{task['description']}' isn’t done yet. Do what must be done 😌",
        f"Your code awaits 😏 Stop procrastinating and tackle '{task['description']}'."
    ]
    return random.choice(reminders)

# --- SEARCH FULL HISTORY (on-demand)
def search_full_history(query):
    """Return matching full_history entries that contain the query (case-insensitive)."""
    q = query.lower().strip()
    results = []
    for entry in memory.get("full_history", []):
        content = entry.get("content", "")
        if q in content.lower():
            # show timestamp + a short preview
            preview = content if len(content) < 200 else content[:197] + "..."
            results.append(f"[{entry.get('time','?')}] {preview}")
    return results

# --- SYSTEM INTEGRATION HELPERS (apps, web, media, notify) ---

def say(text):
    """Speak Azrion's reply using Piper TTS (WAV -> paplay)."""
    if not text:
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    piper_dir = os.path.join(base_dir, "piper", "piper")
    piper_bin = os.path.join(piper_dir, "piper")
    model_path = os.path.join(piper_dir, "en_US-kathleen-low.onnx")

    # Make a temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name

    # Generate WAV with Piper
    cmd_tts = [
        piper_bin,
        "--model", model_path,
        "--output_file", wav_path,
    ]
    subprocess.run(cmd_tts, input=text.encode("utf-8"), check=False)

    # Play WAV (use paplay; if it fails, fall back to aplay)
    try:
        subprocess.run(["paplay", wav_path], check=False)
    except FileNotFoundError:
        subprocess.run(["aplay", wav_path], check=False)



def run_sys_command(cmd_list):
    """
    Run a system command safely and return its output as text.
    cmd_list must be a list, e.g. ["firefox"] or ["xdg-open", "https://google.com"].
    """
    try:
        result = subprocess.run(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        return result.stdout.strip() if result.stdout else "Command executed."
    except Exception as e:
        return f"Command failed: {e}"


def notify(msg):
    """
    Show a desktop notification from Azrion.
    Requires: sudo pacman -Sy libnotify  (on Garuda/Arch). [web:23]
    """
    # notify-send "Azrion" "message"
    run_sys_command(["notify-send", "Azrion", msg])


def system_action(user_input):
    """
    Parse natural language commands and trigger system actions.
    Returns a user-facing string if something was executed, or None if no action matched.
    """
    text = user_input.lower().strip()

    # --- Open common apps ---
    if "open browser" in text or "open firefox" in text:
        run_sys_command(["firefox"])
        return "Opening your browser 🔥"

    if "open code" in text or "open vscode" in text or "open vs code" in text:
        # Change 'code' to your editor command if different
        run_sys_command(["code"])
        return "Launching VS Code 😎"

    if "open files" in text or "open file manager" in text or "open dolphin" in text:
        run_sys_command(["dolphin"])
        return "Opening your file manager 😌"

    # --- Open websites in FireDragon ---
    if "open youtube" in text or ("youtube" in text and "open" in text):
        run_sys_command(["firedragon", "--new-window", "https://www.youtube.com"])
        return "Opening YouTube 👀"

    if "open google" in text:
        run_sys_command(["firedragon", "--new-window", "https://www.google.com"])
        return "Opening Google for you 😌"

    if "open github" in text:
        run_sys_command(["firedragon", "--new-window", "https://github.com"])
        return "Opening GitHub 😎"

    # Generic open URL: "open: https://example.com"
    if text.startswith("open:"):
        url = user_input[5:].strip()
        if url:
            run_sys_command(["firedragon", "--new-window", url])
            return f"Opening {url} 🔥"


    # --- Web search helpers (Google / YouTube) ---
    if text.startswith("search google for "):
        import urllib.parse
        query = user_input[len("search google for "):].strip()
        if not query:
            return "What do you want me to search on Google?"
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        run_sys_command(["firedragon", "--new-window", url])
        return f"Searching Google for \"{query}\" 🔍"

    if text.startswith("search youtube for "):
        import urllib.parse
        query = user_input[len("search youtube for "):].strip()
        if not query:
            return "What do you want me to search on YouTube?"
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        run_sys_command(["firedragon", "--new-window", url])
        return f"Searching YouTube for \"{query}\" 🎵"


    # --- Media control (requires playerctl installed) [web:52][web:57][web:60] ---
    if "play music" in text or "resume music" in text:
        run_sys_command(["playerctl", "play"])
        return "Playing your music 🎵"

    if "pause music" in text or "stop music" in text:
        run_sys_command(["playerctl", "pause"])
        return "Pausing your music 😌"

    if "next song" in text or "next track" in text:
        run_sys_command(["playerctl", "next"])
        return "Skipping to the next track 😎"

    if "previous song" in text or "previous track" in text:
        run_sys_command(["playerctl", "previous"])
        return "Going back to the previous track 👀"

    # --- System info / monitoring ---
    if "show cpu" in text or "cpu usage" in text:
        out = run_sys_command(["bash", "-lc", "top -b -n1 | head -n5"])
        return "Here’s a quick CPU snapshot:\n" + out

    if "show ram" in text or "memory usage" in text:
        out = run_sys_command(["bash", "-lc", "free -h"])
        return "Here’s your memory usage:\n" + out

    if "disk usage" in text or "show disk" in text:
        out = run_sys_command(["bash", "-lc", "df -h | head -n10"])
        return "Here’s your disk usage:\n" + out

    # --- File and folder management (simple, explicit) ---
    if text.startswith("create folder "):
        # Example: "create folder projects in Documents"
        try:
            rest = user_input[len("create folder "):].strip()
            # Try to split "name in path"
            if " in " in rest.lower():
                name_part, path_part = rest.split(" in ", 1)
                folder_name = name_part.strip()
                target_rel = path_part.strip()
            else:
                folder_name = rest
                target_rel = ""
            base = os.path.expanduser("~")
            target_dir = os.path.join(base, target_rel) if target_rel else base
            os.makedirs(os.path.join(target_dir, folder_name), exist_ok=True)
            return f"Created folder '{folder_name}' in '{target_dir}'."
        except Exception as e:
            return f"Could not create folder: {e}"

    if text.startswith("create file "):
        # Example: "create file notes.txt in Documents"
        try:
            rest = user_input[len("create file "):].strip()
            if " in " in rest.lower():
                name_part, path_part = rest.split(" in ", 1)
                file_name = name_part.strip()
                target_rel = path_part.strip()
            else:
                file_name = rest
                target_rel = ""
            base = os.path.expanduser("~")
            target_dir = os.path.join(base, target_rel) if target_rel else base
            os.makedirs(target_dir, exist_ok=True)
            file_path = os.path.join(target_dir, file_name)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write("")
            return f"Created file '{file_name}' in '{target_dir}'."
        except Exception as e:
            return f"Could not create file: {e}"

    if text.startswith("list files in "):
        # Example: "list files in Documents"
        try:
            target_rel = user_input[len("list files in "):].strip()
            base = os.path.expanduser("~")
            target_dir = os.path.join(base, target_rel)
            if not os.path.isdir(target_dir):
                return f"'{target_dir}' is not a directory."
            items = os.listdir(target_dir)
            if not items:
                return f"No files in '{target_dir}'."
            listing = "\n".join(items[:50])
            return f"Files in '{target_dir}':\n{listing}"
        except Exception as e:
            return f"Could not list files: {e}"

    if text.startswith("open folder "):
    # Examples:
    #   "open folder Documents"
    #   "open folder Documents/DSA"
    #   "open folder SY_BTech/Subjects/DSA"
        target_rel = user_input[len("open folder "):].strip()
        if target_rel:
            base = os.path.expanduser("~")
        # Allow nested paths
            target_dir = os.path.join(base, target_rel)
            run_sys_command(["xdg-open", target_dir])
            return f"Opening folder '{target_dir}' 😌"

    # --- Local file search (using fd) ---
    if text.startswith("search files for "):
        # Example: "search files for demo.py"
        pattern = user_input[len("search files for "):].strip()
        if not pattern:
            return "Tell me what filename or pattern to search for."
        cmd = ["fd", pattern, os.path.expanduser("~")]
        out = run_sys_command(cmd)
        if not out.strip():
            return f"No files found matching '{pattern}'."
        lines = out.splitlines()[:30]
        result_text = "\n".join(lines)
        return f"Found these paths for '{pattern}':\n{result_text}"

        # --- Delete files and folders (moves to trash if possible) ---
    if text.startswith("delete file "):
        # Example: "delete file notes.txt in Documents"
        try:
            rest = user_input[len("delete file "):].strip()
            if " in " in rest.lower():
                name_part, path_part = rest.split(" in ", 1)
                file_name = name_part.strip()
                target_rel = path_part.strip()
            else:
                file_name = rest
                target_rel = ""
            base = os.path.expanduser("~")
            target_dir = os.path.join(base, target_rel) if target_rel else base
            file_path = os.path.join(target_dir, file_name)
            if not os.path.exists(file_path):
                return f"File '{file_path}' does not exist."
            # Prefer trash-cli or gio trash if available
            # Attempt trash-cli
            out = run_sys_command(["trash-put", file_path])
            if "command not found" in out.lower():
                # Fallback: gio trash
                out2 = run_sys_command(["gio", "trash", file_path])
                if "command not found" in out2.lower():
                    # Last resort: permanent delete (be careful)
                    os.remove(file_path)
                    return f"Permanently deleted file '{file_path}'."
            return f"Moved file '{file_path}' to Trash."
        except Exception as e:
            return f"Could not delete file: {e}"

    if text.startswith("delete folder "):
        # Example: "delete folder test_azrion in Documents"
        try:
            import shutil
            rest = user_input[len("delete folder "):].strip()
            if " in " in rest.lower():
                name_part, path_part = rest.split(" in ", 1)
                folder_name = name_part.strip()
                target_rel = path_part.strip()
            else:
                folder_name = rest
                target_rel = ""
            base = os.path.expanduser("~")
            target_dir = os.path.join(base, target_rel) if target_rel else base
            folder_path = os.path.join(target_dir, folder_name)
            if not os.path.exists(folder_path):
                return f"Folder '{folder_path}' does not exist."
            # Use trash when possible
            out = run_sys_command(["trash-put", folder_path])
            if "command not found" in out.lower():
                out2 = run_sys_command(["gio", "trash", folder_path])
                if "command not found" in out2.lower():
                    # Fallback: recursive delete – careful
                    shutil.rmtree(folder_path)
                    return f"Permanently deleted folder '{folder_path}'."
            return f"Moved folder '{folder_path}' to Trash."
        except Exception as e:
            return f"Could not delete folder: {e}"

    # --- Raw command (explicit, potentially unsafe) ---
    if text.startswith("run:"):
        # Example: run: ls -la
        cmd = user_input[4:].strip()
        if not cmd:
            return "You need to give me a command after 'run:'."
        # Use a shell explicitly; only you should use this, it's powerful.
        out = run_sys_command(["bash", "-lc", cmd])
        return f"Command output:\n{out}"

    return None

# --- CHAT FUNCTION (updated: short-term memory + archive + typing)
def azrion_chat(user_input):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Store messages in both short-term 'history' and full archive 'full_history'
    user_msg = {"role": "user", "content": user_input, "time": timestamp}
    memory["full_history"].append(user_msg)
    memory["history"].append(user_msg)

    # trim short-term history to last SHORT_TERM_LIMIT messages to keep prompt small
    if len(memory["history"]) > SHORT_TERM_LIMIT:
        memory["history"] = memory["history"][-SHORT_TERM_LIMIT:]

    # Update habits/stats/philosophy
    update_stats(user_input)
    track_habits(user_input)
    track_philosophy(user_input)

    # Auto-flirty/motivation push (decide later whether to append)
    push_text = ai_react_to_user_message(user_input)

    # Task reminder (append to push_text if relevant)
    task_reminder = check_pending_tasks()
    if task_reminder:
        push_text += " " + task_reminder

    # --- System actions (apps, web, media, system info) ---
    sys_response = system_action(user_input)
    if sys_response:
        # Print Azrion-style response and save to memory, but skip model call
        timestamp_sys = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        assistant_msg = {"role": "assistant", "content": sys_response, "time": timestamp_sys}
        memory["full_history"].append(assistant_msg)
        memory["history"].append(assistant_msg)
        if len(memory["history"]) > SHORT_TERM_LIMIT:
            memory["history"] = memory["history"][-SHORT_TERM_LIMIT:]
        save_memory()
        type_out(sys_response)
        return sys_response

    # If user requested a search, handle locally (no model call)
    if user_input.lower().startswith("search history:"):
        query = user_input.split(":", 1)[1]
        results = search_full_history(query)
        if not results:
            return "No matches found in history."
        # Return up to 6 results in a readable block
        return "\n".join(results[:6])

    # Prepare messages (use only short-term memory for speed)
    context_summary = summarize_context()
    # use system prompts + recent history only
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Context summary: {context_summary}"},
    ] + memory["history"]

    # Call Llama (model choice left as-is; for speed consider changing to a smaller model)
    response = chat(model="llama3.1:latest", messages=messages)

    # Extract text only (robust)
    text_response = ""
    if hasattr(response, "message") and hasattr(response.message, "content"):
        text_response = response.message.content
    elif hasattr(response, "text"):
        text_response = response.text
    else:
        text_response = str(response)

    # Append push_text only if relevant (keeps normal replies clean)
    if push_text.strip() and any(word in user_input.lower()
                                for word in ["lazy", "tired", "procrastinate", "stuck", "bug", "error", "fail", "lost", "can't"]):
        text_response = text_response.strip()
        if text_response:
            text_response += "\n\n" + push_text
        else:
            text_response = push_text

    # Occasionally add a philosophy quote (kept brief)
    if random.random() < 0.02:
        text_response = text_response.strip()
        quote = get_philosophy_quote()
        if text_response:
            text_response += "\n\n" + quote
        else:
            text_response = quote

    # Save assistant reply to memory (both short and full)
    assistant_msg = {"role": "assistant", "content": text_response, "time": timestamp}
    memory["full_history"].append(assistant_msg)
    memory["history"].append(assistant_msg)

    # Trim short-term history again if needed
    if len(memory["history"]) > SHORT_TERM_LIMIT:
        memory["history"] = memory["history"][-SHORT_TERM_LIMIT:]

    save_memory()

    # Use typing effect to print reply to console and also return it as string
    type_out(text_response)
    return text_response

