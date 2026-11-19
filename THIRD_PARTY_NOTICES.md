# Ubuntu Glove — Third-Party Component Inventory

This is an inventory for the alpha source package, not a substitute for a release SBOM. Before distribution, generate an SBOM from the exact build environment and preserve the exact licenses/notices for every shipped artifact.

| Component | Role | Delivery boundary |
|---|---|---|
| Python 3 | Application runtime | Ubuntu system package |
| PyGObject / `python3-gi` | Python bindings for GTK/GObject | Ubuntu system package |
| GTK 4 | Overlay and command-palette UI | Ubuntu system package |
| Libadwaita | GNOME-adaptive UI layer | Ubuntu system package |
| gtk4-layer-shell | Compatible Wayland overlay placement | Ubuntu system package |
| AT-SPI2 / `python3-pyatspi` | Accessibility metadata | Ubuntu system package |
| Ayatana AppIndicator | Optional top-bar indicator | Ubuntu system package |
| GNOME Screenshot / XDG Desktop Portal | Explicit screenshot request path | Ubuntu system package / desktop service |
| SQLite | Local context notes database | Python standard-library binding / Ubuntu library |

Ubuntu Glove source code is MIT licensed. The application does not bundle model weights, `llama.cpp`, Qwen, Whisper, OpenVINO, or any voice/presence component in this alpha.
