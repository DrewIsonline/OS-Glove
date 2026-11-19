# Ubuntu Glove Rebuild Notes

## Method

The supplied archive was not a published or wired production application. It was a coherent prototype source tree with an explicit README, Python UI/core code, a per-user installer, a systemd user-service template, a Bash hook, Debian packaging templates, and two small local JSON data files.

The rebuild uses those artifacts as the observable specification. It does not claim to recover features that were not described or present in the source.

## Prototype behavior retained

- The GTK4 `U` overlay, layer-shell fallback behavior, and local visual spotlight.
- AT-SPI application/window/focus context.
- Exact-title local notes stored in SQLite.
- Local onboarding tips and curated command search.
- Clipboard/Bash command staging without automatic execution.
- Active, Quiet, and Off modes with a separate GTK3/Ayatana indicator.
- Explicit screenshot portal capture as an optional feature.

## Production-minded corrections applied

1. **No external endpoints.** Optional model use now accepts only an explicit IPv4 or IPv6 loopback OpenAI-compatible route listed in the reviewed model lock.
2. **No unpinned model choice.** The alpha ships with an empty model lock because no model artifact was supplied. Model integration cannot be switched on accidentally.
3. **Fail closed screenshots.** Capture now refuses to run if AT-SPI is unavailable. The prior behavior could fall back to a capture with no accessibility safety context.
4. **Private temporary images.** Screenshots now use randomly named 0600 files in an app-private 0700 runtime directory instead of a fixed shared filename.
5. **Notes survive updates.** The prototype installer deleted its entire application data directory on every update, which also removed the SQLite notes database. The rebuilt installer separates application code from state and replaces only the code.
6. **Per-user only.** The rebuilt installer intentionally removes system-wide installation because the application depends on an interactive user GNOME session and retains user-specific data.
7. **Testable.** The rebuilt project includes unit tests for local-only endpoint checks, reviewed route validation, local command/tip behavior, context-note matching, capture fail-closed behavior, and Linux permission checks.

## Not reverse-engineered because it was absent

No source or requirements exist for microphone input, speech recognition, voice output, voice-command grammar, a wake word, a camera feed, person-presence detection, a local LLM runtime, model provisioning, or OpenS Control Plane integration. Those must be engineered from an approved specification rather than invented from this overlay prototype.
