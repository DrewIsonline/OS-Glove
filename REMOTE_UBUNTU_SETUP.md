# Ubuntu Glove 0.2.0-alpha — Supported Deployment Boundary

Ubuntu Glove is designed for an **interactive native Ubuntu GNOME desktop session**. That is the supported pilot environment. Run the application as the real logged-in desktop user.

## Supported now

Native Ubuntu GNOME with a local monitor, keyboard, and mouse is the target. An Ubuntu GNOME virtual machine accessed through its graphical console, RDP, VNC, or Parsec may work, but the screenshot portal, overlay placement, and top-bar indicator must be validated against the real remote-desktop configuration.

Install and start the application from a terminal opened inside that graphical session. The installer refuses to run when both `DISPLAY` and `WAYLAND_DISPLAY` are absent.

## Unsupported as a full overlay target

WSLg, SSH, X11 forwarding, and headless Ubuntu can inspect the source and run non-GUI checks, but they are not supported for the full GTK overlay, GNOME indicator, screenshot portal, or reliable AT-SPI behavior.

Do not start the user service from SSH by guessing another user's display or session-bus environment. Connect to the actual desktop session first.

## Required real-machine validation

Follow [docs/UBUNTU-GNOME-ACCEPTANCE-TEST.md](docs/UBUNTU-GNOME-ACCEPTANCE-TEST.md) after installation. A successful source copy or `--check-data` result does not prove the GUI works.

## Local model boundary

The alpha has no shipped model or model route. When a future reviewed OpenS local gateway exists, it must run on explicit loopback `127.0.0.1` or `[::1]`. The app rejects remote, LAN, DNS-name, and cloud endpoint configuration.

## Voice and Presence boundary

This rebuild has no microphone, text-to-speech, voice command, webcam, person-presence, or face-recognition capability. These must be engineered and tested as a separate OpenS LITE module. Do not assume any remote setup adds them.
