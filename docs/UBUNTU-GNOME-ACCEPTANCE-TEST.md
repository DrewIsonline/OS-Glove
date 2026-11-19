# Ubuntu Glove 0.2.0-alpha — Ubuntu GNOME Acceptance Test

Run this only on a real interactive Ubuntu 26.04 GNOME desktop session. Do not run it through headless SSH. Record pass/fail and the exact Ubuntu release, GNOME version, GPU/driver, session type, and monitor layout.

## Install and local-only checks

1. Install the dependencies and run `python3 main.py --check-data`. It must report two commands, two onboarding rules, and zero model routes.
2. Start `python3 main.py --no-tray`. A blue `U` should appear. If layer-shell is available, it should behave as a desktop overlay. If not, record the fallback normal window.
3. Click **Commands**, select a command, and verify that the command appears only in the clipboard. It must not execute.
4. Save a local note for Terminal. Switch away and return. Confirm the note appears only for the matching application and exact title.
5. Turn on GNOME toolkit accessibility as the logged-in user. Confirm a local Terminal or Files onboarding tip appears when AT-SPI provides usable context.
6. Run `bash scripts/install_stack.sh --enable` inside the GNOME terminal. Log out/in once. Confirm one overlay process starts and the user service is active. Confirm the notes database is still present after rerunning the installer.
7. Run `bash scripts/install_stack.sh --disable`. Confirm the overlay stops, the application source remains installed, and the notes/configuration remain.

## Screen-read safety checks

Screen reading must remain off for the baseline pilot. The **Read screen** action must state that it is disabled.

Do not configure a model route unless `data/models.lock.json` contains a real reviewed model artifact with a real SHA-256 and the local gateway has been tested. Once a reviewed local route exists:

1. Configure only `http://127.0.0.1` or `[::1]`; verify a remote, LAN, or `localhost` URL is rejected.
2. Explicitly run `ubuntu-glove --screen-read on`.
3. Focus a normal non-password window, invoke Read screen, and confirm the desktop portal request appears if the desktop requires it.
4. Confirm the green recording indicator shows only during capture.
5. Confirm the app-private runtime directory has mode `0700`, the temporary screenshot is mode `0600` while present, and it is deleted after the model request.
6. Focus a password field and invoke Read screen. Capture must be blocked.
7. Disable GNOME accessibility support or make AT-SPI unavailable. Capture must be blocked rather than falling back to a blind screenshot.

## Explicit exclusions

Do not claim voice control, microphone capture, text-to-speech, person presence detection, or any anti-spoofing behavior from this test. Those features do not exist in Ubuntu Glove 0.2.0-alpha.
