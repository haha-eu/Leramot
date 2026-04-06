# Leramot

A human-like typing simulator for Windows. Paste text, set a duration, and Leramot types it into any active text field — with natural speed variation, realistic mistakes, and self-corrections.

## Features

- Types into any application via simulated keystrokes
- Configurable typing duration (30s – 60 min, or enter a custom time)
- Countdown delay before typing starts (10s, 15s, 30s, 1 min)
- Human-like behaviour: variable speed, typos, corrections, thinking pauses
- Markdown input supported — automatically converted to plain text
- Pause by clicking the Leramot window mid-session, resume by clicking away
- **End (double tap)** emergency stop at any time

## Usage

1. Paste your text into the content field
2. Set how long you want it to take
3. Choose a start delay
4. Click **Start Typing**, then click into your target text field

## Build from Source
```bash
pip install -r requirements.txt
build.bat
```

Outputs a single `Leramot.exe` in the `dist/` folder.

## Requirements

Python 3.10+, Windows only.

## Contributing

Leramot is fully open source and contributions are welcome. Bug fixes, new features, improved typing behaviour — open a PR or raise an issue and we'll go from there.

## ⚠️ Legal Disclaimer ⚠️

Leramot is intended for "personal productivity" purposes. However, this is not the only permitted use. Under the MIT License, you are free to use, modify, and distribute this software as you see fit. By using Leramot, **you accept full responsibility** for how it is used. 

Leramot and its contributors assume no liability for any consequences, penalties, or disciplinary actions resulting from its use. 

**By accessing or using this software, you agree to be bound by these terms. If you do not agree, do not use the software.**

## On macOS

**Using a Mac?**
Leramot is Windows-only. If you're on macOS, we recommend checking out *watchmetype* — a great open source alternative for macOS.

[View watchmetype on GitHub](https://github.com/0xff-r4bbit/watchmetype)

## License

MIT — do whatever you want with it. Check out our website at https://leramot.foo.ng for more info. 
