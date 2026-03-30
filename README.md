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

## License

MIT — do whatever you want with it.
