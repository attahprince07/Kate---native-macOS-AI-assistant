# Kate---native-macOS-AI-assistant

**A voice-first AI assistant for macOS, built from scratch.**

Kate is a native macOS assistant designed around one conviction: the best interface is no interface. Press `⌘⇧K`, speak, and get back something useful. She briefs you on your morning, answers questions in context, manages your tasks, and speaks back in a natural voice.

Built as a solo project by [Amoah Prince Kofi Attah](https://github.com/attahprince07), an electrical engineering student at the University of Wisconsin Madison.

---

## Demo

```
You press ⌘⇧K.
You say: "What's on my plate today?"
Kate says: "Good morning, Kofi. It's 48 degrees in Madison, partly cloudy.
           You have 3 tasks: finish the ECE 330 problem set, push the BSR
           telemetry code, and reply to Professor Tervo's email."
```

No browser tab. No chat window. Just your voice and hers.

---

## Features

**Boot Briefing** — Kate speaks when your Mac wakes up. Date, weather, and your pending tasks, read aloud before you touch anything.

**Voice Chat** — Real time conversation powered by Whisper speech to text, the Claude API for reasoning, and native macOS TTS for voice output. Ask a question, get a spoken answer.

**Task Management** — A browser based task manager (`task_manager.html`) that syncs with Kate's briefing pipeline. Add, complete, and delete tasks visually. Kate reads them back to you.

**Global Hotkey** — `⌘⇧K` activates Kate from anywhere on your Mac via a persistent menu bar app. No terminal required after setup.

**Menu Bar App** — Kate lives in your macOS menu bar as a lightweight background process using `rumps`. Always available, never in the way.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     macOS Menu Bar                   │
│                  kate_menubar.py (rumps)             │
│                    Global Hotkey: ⌘⇧K                │
└──────────────┬──────────────────────────┬────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────┐    ┌──────────────────────────┐
│    Boot Briefing     │    │      Voice Chat Mode     │
│                      │    │                          │
│  wttr.in → weather   │    │  mic → sox recording     │
│  tasks.json → tasks  │    │  audio → Whisper STT     │
│  config.json → name  │    │  text → Claude API       │
│  macOS say → speak   │    │  response → macOS say    │
└──────────────────────┘    └──────────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │   Anthropic API      │
                            │   claude-sonnet-4    │
                            │                      │
                            │   System prompt:     │
                            │   Name, city, tasks, │
                            │   weather context    │
                            └──────────────────────┘
```

---

## File Structure

```
kate/
├── jarvis.py              # Core assistant (briefing + chat + voice)
├── kate_menubar.py        # macOS menu bar app with global hotkey
├── task_manager.html       # Browser based task manager UI
├── config.json            # User configuration (name, city, voice)
├── tasks.json             # Local task storage
├── install_menubar.sh     # One line install script for menu bar
└── README.md
```

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| Speech to Text | OpenAI Whisper (base) | Transcribes voice input locally |
| AI Brain | Claude API (claude-sonnet-4) | Reasoning, conversation, context |
| Text to Speech | macOS native `say` (voice: Kate) | Spoken responses |
| Audio Capture | sox + ffmpeg | Mic recording and audio processing |
| Menu Bar | rumps + pynput | Global hotkey and background process |
| Weather | wttr.in | No API key weather data |
| Tasks | Local JSON | Privacy first task storage |
| Task UI | Vanilla HTML + localStorage | Browser based task management |

---

## Setup

### Prerequisites

- macOS (tested on Ventura and Sonoma)
- Python 3.10+ (built on 3.14)
- Homebrew

### Install

```bash
# Clone the repo
git clone https://github.com/attahprince07/kate.git
cd kate

# Install system dependencies
brew install sox ffmpeg

# Install Python dependencies
pip install anthropic openai-whisper rumps pynput requests

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"
```

### Configure

Edit `config.json` to personalize Kate:

```json
{
  "name": "Your Name",
  "city": "Your City",
  "voice": "Kate"
}
```

Available macOS voices can be listed with `say -v ?`. Kate, Samantha, and Ava are good options.

### Run

```bash
# Morning briefing
python3 jarvis.py briefing

# Voice chat mode
python3 jarvis.py chat

# Menu bar app (background, with ⌘⇧K hotkey)
python3 kate_menubar.py
```

### Auto Start on Login

```bash
bash install_menubar.sh
```

This registers Kate as a login item so the menu bar app launches automatically when your Mac boots.

---

## Chat Mode Commands

Inside `python3 jarvis.py chat`:

| Command | What it does |
|---|---|
| `voice` | Switch to microphone input (Whisper transcription) |
| `text` | Switch back to keyboard input |
| `tasks` | Kate reads your pending tasks aloud |
| `weather` | Get the current weather |
| `quit` | Exit chat mode |

Or just type (or speak) anything and Kate responds conversationally.

---

## v2.0 Roadmap

Kate v1.0 proved the concept. v2.0 is the product.

**Architecture migration:** Rebuilding the client in Swift for proper macOS integration (Accessibility APIs, native UI) and the orchestration layer in FastAPI for clean server side routing.

**Planned features:**
- Screen aware context via macOS Accessibility APIs (Kate can see what you are working on)
- Local and cloud model routing based on cost, latency, and privacy
- Calendar integration for richer morning briefings
- STEM study mode tuned for engineering coursework
- Student tier monetization ($5 to $14/month via Lemon Squeezy)
- Product Hunt launch timed to back to school (Fall 2026)

**Target stack for v2.0:**

| Layer | Technology |
|---|---|
| Client | Swift, macOS native, Accessibility APIs |
| Server | FastAPI, Python, context cache |
| Models | Claude API, local Whisper, cloud TTS fallback |
| Distribution | Lemon Squeezy licensing |

The 14 week development roadmap is documented in `docs/product-plan.md`.

---

## Design Principles

1. **The best interface is no interface.** If Kate requires you to look at a screen to use her, something is wrong.
2. **Latency is the product.** The window between pressing the hotkey and hearing a response is the entire experience. Every architectural decision starts from that constraint.
3. **Local first.** Tasks, config, and voice processing stay on your machine. Cloud calls happen only when local models cannot handle the request.
4. **Ship, then polish.** v1.0 was built in a few weekends. It is opinionated, sometimes wrong, and deliberately scoped down. That is the point.

---

## Known Issues and Workarounds

**Whisper SSL error on Python 3.14:** The `certifi` certificate bundle sometimes fails on newer Python builds. The codebase includes a fallback that sets `ssl._create_default_https_context = ssl._create_unverified_context`. This is acceptable for local Whisper model downloads but should not be used in production networking code.

**ffmpeg required for Whisper:** Whisper depends on ffmpeg for audio processing. If you see decoding errors, confirm ffmpeg is installed with `brew install ffmpeg`.

**Voice recording loop on failed transcription:** If Whisper fails to transcribe (empty audio, background noise), Kate automatically drops to text input mode instead of looping the mic.

---

## Why "Kate"?

The original name was JARVIS. It was renamed to Kate after auditioning every macOS system voice and picking the one that sounded most like a research collaborator and least like a corporate hold line. The name stuck.

---

## Author

**Amoah Prince Kofi Attah**
Electrical Engineering, University of Wisconsin Madison (Class of 2028)

- GitHub: [attahprince07](https://github.com/attahprince07)
- LinkedIn: [amoah-prince](https://linkedin.com/in/amoah-prince)
- Email: paamoah@wisc.edu
