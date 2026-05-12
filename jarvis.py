#!/usr/bin/env python3
"""
Kate - Personal AI Assistant
Voice-activated, Claude-powered, macOS native TTS
"""

import os
import sys
import json
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
JARVIS_DIR    = Path(__file__).parent
TASKS_FILE    = JARVIS_DIR / "tasks.json"
CONFIG_FILE   = JARVIS_DIR / "config.json"
VOICE         = "Samantha"          # macOS voice — change to "Daniel", "Alex", etc.
WHISPER_MODEL = "base"              # tiny | base | small  (base is fine for Mac)

# ── Helpers ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def load_tasks() -> list[dict]:
    if TASKS_FILE.exists():
        with open(TASKS_FILE) as f:
            data = json.load(f)
            return data.get("tasks", [])
    return []

def get_weather(city: str = None) -> str:
    """Fetch weather from wttr.in (no API key needed)."""
    import requests
    location = city or ""
    try:
        r = requests.get(f"https://wttr.in/{location}?format=3", timeout=5)
        return r.text.strip()
    except Exception:
        return "Weather unavailable right now."

def speak(text: str):
    """Speak using OpenAI TTS (nova), fallback to macOS say."""
    import requests as req
    clean = text.replace("*", "").replace("#", "").replace("`", "")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        try:
            r = req.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "tts-1", "voice": "nova", "input": clean},
                timeout=15
            )
            if r.status_code == 200:
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp.write(r.content)
                tmp.close()
                subprocess.run(["afplay", tmp.name], check=False)
                os.unlink(tmp.name)
                return
            else:
                print(f"  ⚠️  OpenAI TTS error {r.status_code}, falling back to say")
        except Exception as e:
            print(f"  ⚠️  OpenAI TTS failed ({e}), falling back to say")

    # Fallback to macOS say
    config = load_config()
    voice  = config.get("voice", "Kate")
    subprocess.run(["say", "-v", voice, clean], check=False)

def speak_async(text: str):
    """Non-blocking speak."""
    t = threading.Thread(target=speak, args=(text,), daemon=True)
    t.start()
    return t

def record_audio(duration: int = 5) -> str | None:
    """
    Record audio from mic using sox (if available) or sounddevice+wave.
    Returns path to a .wav temp file, or None on failure.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    # Try sox first (brew install sox)
    sox = subprocess.run(["which", "sox"], capture_output=True, text=True)
    if sox.returncode == 0:
        print(f"  🎙  Recording for {duration}s... (speak now)")
        subprocess.run(
            ["sox", "-d", "-r", "16000", "-c", "1", "-b", "16", tmp_path, "trim", "0", str(duration)],
            check=False, capture_output=True
        )
        return tmp_path

    # Fallback: sounddevice
    try:
        import sounddevice as sd
        import wave, numpy as np
        print(f"  🎙  Recording for {duration}s... (speak now)")
        fs = 16000
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
        sd.wait()
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(fs)
            wf.writeframes(audio.tobytes())
        return tmp_path
    except Exception as e:
        print(f"  ⚠️  Could not record audio: {e}")
        return None

def transcribe(audio_path: str) -> str | None:
    """Transcribe audio using openai-whisper."""
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        import whisper
        model = whisper.load_model(WHISPER_MODEL)
        result = model.transcribe(audio_path)
        return result["text"].strip()
    except ImportError:
        print("  ⚠️  whisper not installed. Run: pip install openai-whisper")
        return None
    except Exception as e:
        print(f"  ⚠️  Transcription error: {e}")
        return None

def ask_claude(messages: list[dict], system: str) -> str:
    """Call Claude API and return response text."""
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=system,
        messages=messages,
    )
    return response.content[0].text

# ── Boot Briefing ─────────────────────────────────────────────────────────────

def boot_briefing():
    """Full morning/boot briefing — weather + tasks + greeting."""
    config = load_config()
    city   = config.get("city", "")
    name   = config.get("name", "Kofi")

    now        = datetime.now()
    hour       = now.hour
    date_str   = now.strftime("%A, %B %d, %Y")
    time_str   = now.strftime("%I:%M %p")

    if hour < 12:
        greeting_time = "Good morning"
    elif hour < 17:
        greeting_time = "Good afternoon"
    else:
        greeting_time = "Good evening"

    weather  = get_weather(city)
    tasks    = load_tasks()
    pending  = [t for t in tasks if not t.get("done", False)]

    # Build task summary
    if pending:
        task_lines = "\n".join(f"- {t['text']}" for t in pending)
        task_prompt = f"The user has {len(pending)} task(s) today:\n{task_lines}"
    else:
        task_prompt = "The user has no tasks on their list today."

    system = (
        f"You are Kate, a personal AI assistant — sharp, warm, and concise. "
        f"You are giving {name} their morning boot briefing. "
        f"Be friendly but efficient. Speak in 3–5 sentences max. "
        f"Do NOT use bullet points or markdown — this is spoken aloud. "
        f"Today is {date_str} and the time is {time_str}. "
        f"Weather: {weather}. {task_prompt}"
    )

    user_msg = f"Give me my briefing for today, {greeting_time}."

    print(f"\n{'─'*50}")
    print(f"  KATE BOOT BRIEFING — {date_str}")
    print(f"{'─'*50}")
    print(f"  🌤  {weather}")
    print(f"  📋  {len(pending)} pending task(s)")
    print(f"{'─'*50}\n")

    response = ask_claude([{"role": "user", "content": user_msg}], system)
    print(f"Kate: {response}\n")
    speak(response)

# ── Conversation Mode ─────────────────────────────────────────────────────────

def chat_mode():
    """Real-time voice conversation loop with JARVIS."""
    config   = load_config()
    name     = config.get("name", "Kofi")
    city     = config.get("city", "")
    history  = []

    now      = datetime.now()
    weather  = get_weather(city)
    tasks    = load_tasks()
    pending  = [t for t in tasks if not t.get("done", False)]
    task_summary = ", ".join(t["text"] for t in pending) if pending else "none"

    system = (
        f"You are Kate, {name}'s personal AI assistant — intelligent, warm, and concise. "
        f"Keep responses short and conversational (2–4 sentences). "
        f"Do NOT use bullet points or markdown — responses are spoken aloud. "
        f"Today is {now.strftime('%A, %B %d')}. Current weather: {weather}. "
        f"Pending tasks: {task_summary}. "
        f"You know {name} is an Electrical Engineering & CS student at UW-Madison, "
        f"involved in Badger Solar Racing, ColorStack, and NSBE. "
        f"Be helpful, direct, and occasionally witty."
    )

    intro = f"JARVIS online. What do you need, {name}?"
    print(f"\n{'─'*50}")
    print(f"  KATE CHAT MODE  (type 'quit' to exit, 'voice' for mic)")
    print(f"{'─'*50}\n")
    print(f"Kate: {intro}")
    speak(intro)

    use_voice = False

    while True:
        try:
            if use_voice:
                audio = record_audio(duration=6)
                if audio:
                    user_input = transcribe(audio)
                    os.unlink(audio)
                    if not user_input:
                        print("  ⚠️  Could not understand audio. Switching to text mode.")
                        speak("I couldn't catch that. Switching to text mode.")
                        use_voice = False
                        continue
                    print(f"\nYou (voice): {user_input}")
                else:
                    print("  ⚠️  Recording failed. Switching to text mode.")
                    use_voice = False
                    continue
            else:
                user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            cmd = user_input.lower()

            # ── Meta commands ──
            if cmd in ("quit", "exit", "bye", "goodbye"):
                farewell = "Signing off. Have a great one, Kofi."
                print(f"\nKate: {farewell}")
                speak(farewell)
                break

            if cmd == "voice":
                use_voice = True
                ready = "Listening..."
                print(f"\nKate: {ready}")
                speak(ready)
                continue

            if cmd == "text":
                use_voice = False
                print("\n  → Switched to text mode.")
                continue

            if cmd in ("tasks", "my tasks", "what are my tasks"):
                pending = [t for t in load_tasks() if not t.get("done", False)]
                if pending:
                    msg = f"You have {len(pending)} pending tasks: " + ", ".join(t["text"] for t in pending)
                else:
                    msg = "Your task list is clear. Nothing pending."
                print(f"\nKate: {msg}")
                speak(msg)
                history.append({"role": "user",      "content": user_input})
                history.append({"role": "assistant",  "content": msg})
                continue

            if cmd == "weather":
                w = get_weather(city)
                msg = f"Current weather: {w}"
                print(f"\nKate: {msg}")
                speak(msg)
                continue

            # ── Claude response ──
            history.append({"role": "user", "content": user_input})
            response = ask_claude(history, system)
            history.append({"role": "assistant", "content": response})

            print(f"\nKate: {response}")
            speak(response)

        except KeyboardInterrupt:
            print("\n\n  Interrupted. Goodbye.")
            speak("Goodbye.")
            break

# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args or args[0] == "chat":
        chat_mode()
    elif args[0] == "briefing":
        boot_briefing()
    elif args[0] == "setup":
        from setup import run_setup
        run_setup()
    else:
        print("Usage: python3 jarvis.py [chat|briefing|setup]")

if __name__ == "__main__":
    main()
