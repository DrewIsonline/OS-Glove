# Ubuntu Glove 0.2.0-alpha — Product Specification

## Product boundary

Ubuntu Glove is a **local-first assistant overlay for native Ubuntu GNOME desktops**. It is a normal per-user GTK application. It does not patch the kernel, replace GNOME/Mutter, run as root, execute terminal commands, read browser cookies, or install a system-wide keylogger.

This rebuild is based on the supplied prototype source and README. It implements the actual product described there as a buildable source project. It is not a public release and not the full Drew Is OpenS LITE product.

## Implemented alpha features

1. A GTK4/Libadwaita clickable and draggable `U` overlay. It uses GTK4 layer-shell when the desktop supports it and falls back to a standard undecorated GTK window when it does not.
2. Local context notes stored in `~/.local/share/ubuntu-glove/context_notes.db`. A note is tied to the AT-SPI application identity and an escaped exact window title.
3. Local AT-SPI context watching for an application identity, title, focused element role/name, and bounds. This feeds notes and local onboarding tips.
4. A local command palette backed only by `data/viable_commands.json`. It copies a chosen command to the clipboard. It never executes the command.
5. Optional Bash staging through `Ctrl+Space`. The selected command is inserted into the existing Bash prompt for user review; it is not executed.
6. Active, Quiet, and Turned Off modes in per-user settings, plus an optional Ayatana indicator.
7. Optional **explicitly enabled** screen reading via the GNOME screenshot portal. The app refuses capture if AT-SPI safety context is unavailable or a focused password/credential field is detected. Captures use a random 0600 file in an app-private 0700 runtime directory and are deleted after the request.
8. Optional model requests only through a reviewed `http://127.0.0.1` or `[::1]` OpenAI-compatible local gateway route listed in `data/models.lock.json`. External, LAN, DNS-name, API-key, and cloud endpoints are rejected by code.

## Excluded from this alpha

Ubuntu Glove does not currently contain microphone input, speech-to-text, text-to-speech, wake words, spoken Play/Pause/Stop commands, webcam capture, person presence detection, face recognition, person tracking, OpenVINO, Whisper, Qwen TTS, `llama.cpp`, Qwen weights, FAISS, or the OpenS FULL server stack.

Those are separate OpenS LITE modules that need pinned binaries/models, hardware capacity checks, explicit customer consent, visible hardware state, a kill switch, local retention rules, and release acceptance tests. They are not “turned on” by changing a setting in this app.

## Trust and data rules

- Local notes and settings live under the desktop user's XDG directories.
- The app has no default network path. Local tips and commands work with no model configuration.
- Screen reading is off by default.
- The app does not send a screen image or structural context anywhere until the user both configures a reviewed loopback model route and explicitly enables screen reading.
- A remote endpoint is not a supported mode in this alpha.
- Third-party changes to the curated command JSON are code-adjacent content. Review them before installation because the app can stage them in a terminal.

## Release gates before any customer distribution

1. Replace placeholder packaging owner/source metadata with verified Drew Is ownership/contact data.
2. Build and sign a `.deb` in a clean Ubuntu 26.04 GNOME environment.
3. Generate a SHA-256 manifest, SBOM, third-party notices, release notes, and an actual model lock only if a local model bundle ships.
4. Run the automated tests, then execute `docs/UBUNTU-GNOME-ACCEPTANCE-TEST.md` on a real Ubuntu GNOME desktop under Wayland.
5. Keep the voice/presence module disabled until its separate privacy, capacity, and reliability release gates pass.
