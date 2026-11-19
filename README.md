# Ubuntu Glove

**Version:** 0.2.0-alpha  
**Status:** Buildable personal-pilot application. Not a customer release or the complete Drew Is OpenS LITE product.

Ubuntu Glove is a local-first assistant overlay for a **native Ubuntu GNOME desktop**. It provides a clickable GTK overlay, local context notes, local onboarding tips, and a reviewed terminal-command palette. It runs as the logged-in user and does not modify the kernel, GNOME compositor, display server, browser cookies, or system configuration outside its own user directories.

This rebuild is based on the supplied `ubuntu-glove (1).zip` prototype. It preserves the intended overlay, notes, accessibility, and command-staging features, while fixing the release-blocking problems found in the prototype review.

## What works now

- A draggable GTK4/Libadwaita `U` overlay. It uses GTK4 layer-shell when available and falls back to a regular undecorated GTK window when it is not.
- Context-bound notes stored locally in `~/.local/share/ubuntu-glove/context_notes.db`.
- AT-SPI context awareness for application/window metadata and local tips. It does not run a continuous screenshot process.
- A local command palette using `data/viable_commands.json`. It copies the selected command to the clipboard; it never executes it.
- Optional Bash `Ctrl+Space` integration that inserts a selected command into the current prompt for your review. It does not press Enter.
- Active, Quiet, and Turned Off modes, plus an optional Ayatana status indicator.
- An explicitly enabled screen-reading path which requires AT-SPI to be available, blocks protected/password fields, uses the desktop screenshot portal first, writes only to a random private temporary file, and deletes that file after use.
- Optional local model requests only through a reviewed OpenAI-compatible loopback endpoint on `127.0.0.1` or `[::1]`. Cloud, LAN, DNS-name, and API-key endpoints are rejected by code.

## What is not in this application

This project does **not** provide microphone control, speech-to-text, text-to-speech, wake words, spoken Play/Pause/Stop commands, webcam capture, person-presence detection, face recognition, tracking, Whisper, Qwen TTS, OpenVINO, a local model binary, model weights, FAISS, or the OpenS FULL server.

Those capabilities are separate OpenS LITE modules. Do not add them from random tutorials or packages. They need their own source, pinned artifacts, consent flow, device-capacity test, privacy controls, visible hardware state, and release acceptance tests.

## Install on native Ubuntu GNOME

Use Ubuntu Desktop 26.04 LTS on a machine where you are logged into the graphical GNOME desktop. Do not install this application from a headless SSH session or use WSL as the production environment.

Copy this project to your Linux home directory. A Windows ZIP does not preserve Linux executable bits, so restore them first:

```bash
cd ~/ubuntu-glove-rebuilt
chmod +x scripts/install_stack.sh scripts/ubuntu-glove debian/rules
```

Install its Ubuntu packages and the per-user application:

```bash
bash scripts/install_stack.sh --install-deps --enable
```

The installer validates bundled data, installs source code at `~/.local/share/ubuntu-glove/app`, creates `~/.local/bin/ubuntu-glove`, and enables a **user-level** systemd service. It deliberately does not support a system-wide mode. It preserves `context_notes.db` and `~/.config/ubuntu-glove/settings.json` across application updates.

Verify the installed service:

```bash
systemctl --user status ubuntu-glove.service --no-pager
~/.local/bin/ubuntu-glove --show-config
```

To disable the overlay but keep notes and settings:

```bash
bash ~/.local/share/ubuntu-glove/app/scripts/install_stack.sh --disable
```

## First pilot test

Before enabling the service, smoke-test the application inside a visible GNOME terminal:

```bash
cd ~/ubuntu-glove-rebuilt
python3 main.py --check-data
python3 main.py --no-tray
```

Click the avatar, open **Commands**, choose a record, and confirm the command is only placed on the clipboard. Save a harmless test note. Do not configure any model endpoint or test **Read screen** in the first pilot.

For the full real-machine checklist, use [docs/UBUNTU-GNOME-ACCEPTANCE-TEST.md](docs/UBUNTU-GNOME-ACCEPTANCE-TEST.md).

## Optional Bash command staging

Run this once if you want `Ctrl+Space` to open the palette from an interactive Bash prompt:

```bash
if ! grep -qxF 'source "$HOME/.local/share/ubuntu-glove/app/scripts/bashrc_hook.sh"' "$HOME/.bashrc"; then
  printf '\nsource "$HOME/.local/share/ubuntu-glove/app/scripts/bashrc_hook.sh"\n' >> "$HOME/.bashrc"
fi
source "$HOME/.bashrc"
```

The selected command appears in the current command line. Read it before you run it.

## Local model gateway: intentionally disabled until pinned

The app runs without a model. `data/models.lock.json` is intentionally empty because no validated `llama.cpp`/Qwen model bundle or model checksum was supplied with the prototype. The command below will reject configuration until a reviewed release adds an enabled route with a real model revision and SHA-256:

```bash
ubuntu-glove --configure-local-gateway http://127.0.0.1:8080/v1 opens-lite-qwen3-4b
```

When a real local OpenS gateway and reviewed model lock exist, screen reading must still be explicitly enabled:

```bash
ubuntu-glove --screen-read on
```

This is deliberately not an Ollama/cloud quick-start. The product policy is local-first and no default data egress.

## Build a local `.deb`

Build only in a clean Ubuntu 26.04 environment after replacing the placeholder packaging owner and source URL. This creates a local package; it does not publish it.

```bash
sudo apt install -y build-essential debhelper dh-python python3-all
chmod +x scripts/build_deb.sh
bash scripts/build_deb.sh
```

See [docs/PRODUCT-SPEC.md](docs/PRODUCT-SPEC.md) for product boundaries and release gates.

## Project layout

```text
ubuntu-glove-rebuilt/
├── core/                         # Local settings, notes, accessibility, model client
├── data/                         # Reviewed command/tip data and model lock
├── ui/                           # GTK overlay, palette, status indicator
├── tests/                        # Portable unit tests
├── scripts/                      # Per-user installer, Bash hook, Debian build helper
├── docs/                         # Product boundary and real-GNOME acceptance plan
├── debian/                       # Debian package metadata
└── main.py                       # CLI and GTK application entry point
```

## License

MIT. See [LICENSE](LICENSE).
