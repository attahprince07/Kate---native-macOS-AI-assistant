# JARVIS — Personal AI Assistant

A local, voice-activated AI assistant for macOS. Powered by Claude.
Gives you a daily briefing on boot and is always a command away.

---

## Project Structure

```
jarvis/
├── jarvis.py          # Main assistant (chat + briefing)
├── config.json        # Your name, city, voice preference
├── tasks.json         # Local task list (auto-managed)
├── task_manager.html  # Open in browser to manage tasks visually
├── setup.sh           # One-time setup script
└── logs/              # Boot briefing logs (auto-created)
```

---

## Setup (one time)

### 1. Prerequisites

Install Homebrew if you haven't:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Install Python deps + optional audio tool:
```bash
brew install sox       # Better mic recording (optional but recommended)
pip3 install anthropic requests sounddevice openai-whisper
```

### 2. Set your Anthropic API key

Get a key at https://console.anthropic.com
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# To make it permanent, add this line to ~/.zshrc
```

### 3. Run setup

```bash
cd ~/jarvis
bash setup.sh
```

This will:
- Install all Python deps
- Register a macOS LaunchAgent so the briefing fires on every login
- Add a `jarvis` alias to your shell

### 4. First run

```bash
python3 jarvis.py briefing   # Test your boot briefing
python3 jarvis.py chat       # Start a chat session
```

After setup, just type `jarvis` in any terminal to start chatting.

---

## Daily Use

### Boot Briefing (automatic)
Every time you log into your Mac, JARVIS will:
- Greet you based on time of day
- Tell you the current weather in your city
- Read out your pending tasks for the day

### Chat Mode
```bash
jarvis           # Start a voice/text chat session
```

Inside chat mode:
- Type your message, press Enter — JARVIS responds and speaks
- Type `voice` — switch to mic input (you speak, Whisper transcribes)
- Type `text` — switch back to text input
- Type `tasks` — hear your pending task list
- Type `weather` — hear the current weather
- Type `quit` — exit

### Task Manager
Open `task_manager.html` in your browser to:
- Add / check off / delete tasks
- View stats (total, pending, done)
- Tasks are saved to your browser's localStorage

> **Note:** The task manager uses browser localStorage for the visual UI.
> The terminal app reads from `tasks.json`. To keep them in sync, 
> see the "Syncing tasks" section below.

---

## Configuration

Edit `config.json` to personalize:
```json
{
  "name": "Kofi",
  "city": "Madison, Wisconsin",
  "voice": "Samantha",
  "whisper_model": "base"
}
```

**Available macOS voices** (run `say -v '?'` in terminal to see all):
- `Samantha` — default US female
- `Daniel` — UK male
- `Alex` — US male
- `Karen` — Australian female

**Whisper models** (larger = more accurate, slower to load):
- `tiny` — fastest, decent for clear speech
- `base` — good balance (recommended)
- `small` — more accurate, slower first load

---

## Syncing Tasks (HTML ↔ Terminal)

The task manager HTML uses browser localStorage.
The Python scripts read from `tasks.json`.

**Option A (simple):** Use only the terminal. Edit `tasks.json` manually or add a task directly:

```python
# Quick add from terminal
python3 -c "
import json, datetime
with open('tasks.json') as f: d = json.load(f)
d['tasks'].append({'id': d['next_id'], 'text': 'Your new task', 'done': False, 'created': str(datetime.date.today())})
d['next_id'] += 1
with open('tasks.json','w') as f: json.dump(d, f, indent=2)
print('Task added.')
"
```

**Option B (future enhancement):** Build a small local Flask API that both the HTML and Python scripts hit. That's a Phase 2 upgrade.

---

## Troubleshooting

**No sound / TTS not working:**
```bash
say -v Samantha "Hello, Kofi"  # Test macOS TTS directly
```

**Mic not working / whisper errors:**
```bash
pip3 install openai-whisper --upgrade
brew install sox
```

**Boot briefing not firing:**
```bash
launchctl list | grep jarvis          # Check if agent is loaded
cat ~/jarvis/logs/briefing_err.log    # Check for errors
```

**Re-run setup:**
```bash
launchctl unload ~/Library/LaunchAgents/com.jarvis.briefing.plist
bash setup.sh
```

---

## Roadmap (Phase 2 ideas)

- [ ] ElevenLabs voice for a true Jarvis-like sound
- [ ] Google Calendar integration (read events into briefing)
- [ ] Wake word detection ("Hey Jarvis") with porcupine
- [ ] Flask API to sync tasks between HTML manager and Python
- [ ] Spotify "focus mode" trigger on chat open
- [ ] SMS/iMessage daily briefing via Twilio
