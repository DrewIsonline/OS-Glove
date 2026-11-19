# Ubuntu Glove Security Notes

## Supported operating boundary

Ubuntu Glove 0.2.0-alpha is designed for a single, logged-in user on a native Ubuntu GNOME desktop. It is not a multi-user service, remote-desktop security product, surveillance product, or remote-management agent.

Run it as the graphical desktop user. Do not run the installer, overlay, or user service as root. Do not treat WSLg, SSH, X11 forwarding, or a headless host as a supported overlay deployment environment.

## Data handling

The application stores settings under `~/.config/ubuntu-glove/` and context notes under `~/.local/share/ubuntu-glove/context_notes.db`. The installer replaces only `~/.local/share/ubuntu-glove/app`; it must not delete notes or settings during an update.

The local command palette copies a user-selected command to the clipboard or stages it in the active Bash prompt. It never invokes a terminal command itself.

## Screen reading

Screen reading is disabled by default. It must be explicitly enabled after a reviewed local model gateway is configured. The code blocks capture when AT-SPI safety context is unavailable and when the focused control appears to be a protected or credential field. This is defense in depth, not proof that every application labels every secret correctly.

Temporary screenshots are created with a random filename in an application-private directory. They are restricted to the user on Linux and deleted after the request finishes. Portal denial must be respected.

## Model gateway policy

The application has no default network endpoint and accepts only explicit loopback `http://127.0.0.1` or `[::1]` endpoints. It rejects remote, LAN, DNS-name, HTTPS, credential-bearing, query-string, and fragment URLs. A model route must appear in the reviewed `data/models.lock.json` file.

Do not add an external endpoint by weakening this validation. Any future external connector needs its own policy, disclosure, audit record, and user-approved egress control in the OpenS product layer.

## Reporting a problem

Until a real public issue tracker and contact address replace the placeholder package metadata, report findings privately to the application owner. Do not publish secrets, personal notes, screenshots, or copied terminal output in an issue report.
