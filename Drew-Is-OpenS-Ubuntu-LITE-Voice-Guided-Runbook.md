# Drew Is OpenS — Ubuntu LITE Host Setup

**Purpose:** Replace Windows with Ubuntu Desktop, prepare one local GPU workstation for the Drew Is OpenS LITE / Ubuntu Glove path, and install the supplied Ubuntu Glove source as a controlled per-user alpha pilot.

**Version:** 1.2 — October 21, 2026  
**Recommended operating system:** Ubuntu Desktop 26.04 LTS, 64-bit Intel/AMD PC edition. Ubuntu 26.04 LTS is supported through April 2031. [1]

> **Hard truth before you start:** This permanently deletes Windows and everything on the selected internal drive. It is not a dual-boot guide. The original OpenS ZIP contains architecture documents only. Install the rebuilt `ubuntu-glove-rebuilt-0.2.0-alpha.zip` source bundle supplied with this guide, not the original prototype ZIP. It is a buildable personal-pilot application, not a signed production release or the full OpenS LITE model/runtime stack.

## How to use this as a voice guide

A person or an AI reader must read **one numbered card only**, then stop and wait for your answer. Do not read ahead.

Use these spoken commands:

- **“Start”** or **“Play”** — read the current card.
- **“Next”** — read the next card.
- **“Repeat”** — read the current card again.
- **“Pause”** — say: “Paused at card [number].” Then say nothing else.
- **“Resume”** — repeat the current card, then wait.
- **“Back”** — go back one card and read it.
- **“Status”** — state the current card title and what must be true before continuing.
- **“Help”** — explain the current screen or command only.
- **“Stop”** — end the session and state the exact card where it stopped.
- **“I see…”** — read the exact words on the screen. Do not guess; resolve that screen before continuing.

### Reader safety rules

1. Never advance automatically.
2. At **Card 9**, the reader must ask: “Do you confirm that this is the correct drive and you want to permanently erase Windows?” It may continue only after an explicit **“Yes, erase this drive.”**
3. If a screen differs from the words in this guide, pause. Read the screen text aloud and ask for help.
4. Never ask the user to say or reveal a password, encryption passphrase, recovery key, or Wi-Fi password aloud. Say “enter it privately.”
5. A command block must be read one line at a time. Wait for the command to finish before reading the next line.

## What this guide is for — and not for

This is the correct first-machine path if the machine will run **Drew Is OpenS LITE** or act as a **Ubuntu Glove desktop/edge companion**. The supplied architecture calls for local Qwen inference through `llama.cpp`, local SQLite plus FAISS data, and optional local transcription. It treats Ubuntu Glove as an adapter for device functions, not as a second database or separate product core.

The supplied Ubuntu Glove source is a local GTK desktop overlay. Its working features are local notes, context tips, a curated command palette, optional user-triggered screen reading, and optional LLM endpoint configuration. It accepts mouse clicks, keyboard text, and a Bash `Ctrl+Space` binding. **It does not contain microphone capture, speech-to-text, text-to-speech, wake-word detection, or spoken Play/Pause/Stop commands.** The voice controls in this document are for the AI or person reading the cards to you; they are not provided by this app.

Do **not** use this guide to pretend one workstation is the finished shared **OpenS FULL** server. FULL needs a signed and tested release plus its own deployment profile, including PostgreSQL with pgvector, Keycloak, OpenFGA, Valkey, vLLM, backups, observability, and controlled network exposure. Installing those pieces ad hoc now would create an unsupported pile of components, not OpenS.

## Before Card 1: gather these items

Have these items at the machine:

- The target PC, a monitor, keyboard, mouse, and power cable.
- Ethernet if possible. Wi-Fi is fine if necessary.
- One empty USB flash drive of **at least 8 GB**. This USB will be erased.
- One separate backup drive with enough room for anything you need from Windows.
- Another phone, tablet, or computer with this runbook available.
- Your Wi-Fi name and password, if you will use Wi-Fi.
- A private place to write down the Ubuntu disk-encryption passphrase and the Ubuntu account password. Store them **off the target PC**.

If the computer has more than one internal or external drive, physically disconnect every drive that is **not** the drive being replaced. This is the simplest way to prevent wiping the wrong drive.

---

# Voice-guided cards

## Card 1 — Turn on and decide if you are ready

**Reader says:** “Turn on the computer while it still runs Windows. We are not erasing anything yet. Confirm that you have a backup drive, an eight-gigabyte or larger empty USB stick, and another device with this guide. Say ‘ready’ when those are present.”

**You do:** Turn on the target computer. Do not insert the Ubuntu USB yet.

**Continue when:** You can see Windows and have the required backup and USB media.

---

## Card 2 — Back up what you cannot replace

**Reader says:** “Copy every file you care about from Windows to the external backup drive. Include Desktop, Documents, Downloads, Pictures, browser bookmarks, password-manager recovery information, SSH keys, application installers, and anything stored outside the usual folders. Also copy the OpenS Software Build Folder ZIP, `ubuntu-glove-rebuilt-0.2.0-alpha.zip`, and its matching `.sha256` file. Do not continue until you can open a few copied files from the backup drive.”

**You do:** Copy your files to the backup drive. Eject it safely when finished, then unplug it.

**Important:** Windows will be deleted. A cloud-sync icon is not a verified backup. Open files from the backup drive before trusting it.

**Continue when:** The backup is verified and unplugged.

---

## Card 3 — Download the Ubuntu installer file

**Reader says:** “In Windows, open the official Ubuntu Desktop download page. Download Ubuntu Desktop 26.04 LTS for an Intel or AMD computer. Save the ISO file where you can find it, normally Downloads. Do not download Ubuntu Server for this Glove workstation.”

**You do:** Go to <https://ubuntu.com/download/desktop> and download the current Ubuntu Desktop 26.04 LTS ISO.

**Do not do:** Do not use a random mirror, torrent, third-party ‘driver pack,’ or modified ISO.

**Continue when:** The download is complete. The filename will look similar to `ubuntu-26.04-desktop-amd64.iso`.

---

## Card 4 — Make the bootable USB

**Reader says:** “Still in Windows, download Rufus from rufus dot ie. Insert the empty USB stick. Open Rufus. Make sure Device shows the USB stick, not an internal drive. Click Select and choose the Ubuntu ISO. Leave the normal defaults. If this computer is modern and has trouble booting later, use GPT and UEFI non CSM. Click Start. When Rufus asks how to write the ISO, choose ISO Image mode. Confirm only after you verify the USB is the device being erased.”

**You do:** Create the bootable USB using Rufus. When Rufus says **READY**, click **Close**.

Ubuntu’s official instructions use Rufus on Windows and say that its normal defaults are safe; they also specify **ISO Image mode** when Rufus asks. [2]

**Continue when:** Rufus says **READY** and the USB remains plugged in.

---

## Card 5 — Prepare the target machine for the wipe

**Reader says:** “Shut down Windows completely. Unplug the external backup drive and every non-target storage drive. Leave connected only the monitor, keyboard, mouse, power, network cable if used, and the new Ubuntu USB. If you have multiple internal drives and cannot identify the Windows drive with certainty, stop here. Do not guess.”

**You do:** Shut down Windows. Disconnect all backup and extra data drives. Keep the Ubuntu USB inserted.

**Continue when:** Only the drive you intend to replace is connected.

---

## Card 6 — Boot from the Ubuntu USB

**Reader says:** “Turn on the computer and immediately tap the boot-menu key about once each second. F12 is most common. Escape, F2, F10, and F11 are also common. Choose the USB entry that begins with UEFI. Do not choose the old Windows Boot Manager.”

**You do:** Power on and open the temporary boot menu. Select the Ubuntu USB’s **UEFI** entry.

If no boot menu appears, restart and try another key. Ubuntu’s current guidance lists F12, Escape, F2, and F10 as common PC boot-menu keys. [2]

**Continue when:** You see the Ubuntu welcome or installer screen.

---

## Card 7 — Try Ubuntu before installing it

**Reader says:** “At the Ubuntu welcome screen, choose Try Ubuntu first. This does not change the drive. Wait for the temporary Ubuntu desktop. Check that the screen is readable, the mouse and keyboard work, Wi-Fi or Ethernet works, and the camera, microphone, and speakers appear in Settings. If these basics fail, stop before erasing Windows.”

**You do:** Choose **Try Ubuntu**. Test the basic hardware. If all is good, double-click **Install Ubuntu** on the desktop.

**Why:** The temporary session lets you catch basic hardware failures while Windows is still intact. It is especially worth doing with a GPU, Wi-Fi adapter, webcam, or unusual motherboard.

**Continue when:** Basic hardware works and the installer is open.

---

## Card 8 — Make the simple installer choices

**Reader says:** “Choose English unless you need another language. Choose your keyboard layout. Connect to the internet. Choose Install Ubuntu. Choose Interactive installation. Choose Default selection, not Extended. On the software screen, turn on both third-party software options. This gives Ubuntu permission to install useful Wi-Fi, media, and NVIDIA graphics support. Continue.”

**You do:** Make these choices:

1. **Language:** English.
2. **Accessibility:** choose what you need; otherwise continue.
3. **Keyboard:** English US, unless yours differs.
4. **Network:** connect to Ethernet or Wi-Fi.
5. **Try or install:** **Install Ubuntu**.
6. **Type of installation:** **Interactive installation**.
7. **Applications:** **Default selection**.
8. **Optimise your computer:** check **both** third-party software options.

Ubuntu recommends enabling both third-party software options and notes that they can improve support for hardware such as NVIDIA graphics. [2]

**Continue when:** You are on the **Disk setup** screen.

---

## Card 9 — Permanently erase Windows

**Reader says:** “Stop and look closely. Select ‘Erase disk and install Ubuntu.’ Verify the visible drive size and manufacturer match the one drive you deliberately left connected. Do not select manual partitioning. This is the irreversible point.”

**You do:** Select **Erase disk and install Ubuntu**. If there is a drive selector, choose the target drive only.

> **Required spoken confirmation:** The reader must now ask: “Do you confirm that this is the correct drive and you want to permanently erase Windows?” Continue only after: **“Yes, erase this drive.”**

**Important:** This choice gives Ubuntu the whole selected drive and deletes Windows, its partitions, and all files on that drive. [2]

**Continue when:** You have explicitly confirmed the correct drive.

---

## Card 10 — Turn on encryption and create your account

**Reader says:** “Choose encrypt with a passphrase. Enter a long passphrase privately and write it down off the computer. You will need it every time the computer starts. For computer name, use opens-lite-01. Use your normal first name and a short lowercase username, such as drew. Require a password to log in. Select Portland or America Los Angeles for the timezone. Review the summary. If the disk and encryption choices are correct, click Install.”

**You do:** Make these choices:

1. On the encryption screen, choose **Encrypt with a passphrase**.
2. Enter a strong disk passphrase privately. Write it down offline.
3. **Computer name:** `opens-lite-01`.
4. **Your name:** your normal name.
5. **Username:** a simple lowercase name with no spaces, for example `drew`.
6. Keep **Require my password to log in** enabled.
7. **Timezone:** Portland / America Los Angeles.
8. Review the summary and click **Install**.

Ubuntu recommends passphrase-based disk encryption and warns that data cannot be recovered without the disk passphrase. [2]

**Continue when:** Ubuntu is copying files.

---

## Card 11 — Restart into Ubuntu

**Reader says:** “Wait for installation to complete. Click Restart Now. When Ubuntu tells you to remove the installation medium, remove the USB stick and press Enter. On the next boot, enter the disk-encryption passphrase privately, then log in with your Ubuntu account password.”

**You do:** Restart, remove the USB only when asked, unlock the encrypted disk, and log in.

**Continue when:** You are looking at the Ubuntu desktop with no USB inserted.

---

## Card 12 — Finish the first-run screens

**Reader says:** “Answer the Ubuntu first-run screens. Leave device-information sharing off unless you specifically want it on. Do not install random applications from the App Center. We will first update Ubuntu, verify the graphics driver, and create a backup.”

**You do:** Complete the welcome screens. You may leave location services off unless you want them.

**Continue when:** You are at the normal Ubuntu desktop.

---

## Card 13 — Update Ubuntu completely

**Reader says:** “Open Terminal by pressing Control Alt T. Type each line exactly. When asked for the password, enter it privately. Nothing will appear while you type the password. Wait for each command to finish.”

**You do:** Run these commands one at a time:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

After reboot, unlock the disk and log in again.

**Continue when:** The computer is back at the Ubuntu desktop.

---

## Card 14 — Verify the NVIDIA GPU, if this machine has one

**Reader says:** “Open Terminal. Type nvidia-smi and press Enter. If you see a table with your GPU name, driver version, temperature, and memory, the NVIDIA driver is working. If you see command not found or no devices, do not download a random driver. Open the Applications menu, search for Additional Drivers, and select the NVIDIA driver marked recommended. Apply Changes, reboot, and run nvidia-smi again.”

**You do:** Run:

```bash
nvidia-smi
```

**Expected result:** A table that lists the NVIDIA GPU. For an RTX 3090, it should say something similar to `NVIDIA GeForce RTX 3090`.

**If the command works:** Continue to Card 15.

**If it does not work:** Use **Additional Drivers** first. Do not mix an Ubuntu-packaged driver with NVIDIA’s separate repository unless we have a specific reason. NVIDIA supports Ubuntu 26.04 and documents its repository method, but the Ubuntu-installed recommended driver is the simpler first choice for this desktop host. [3]

**If the desktop will not load after a driver change:** Stop. Boot the Ubuntu USB, choose **Try Ubuntu**, and ask for help before changing more drivers.

---

## Card 15 — Install the safe host tools

**Reader says:** “Open Terminal. We are installing basic host tools only: update tools, Git, build tools, Python virtual-environment support, media support, unzip, SQLite, and Podman. We are not installing random AI models or the FULL server stack.”

**You do:** Run this one command. Enter the password privately if asked.

```bash
sudo apt install -y git curl ca-certificates build-essential cmake pkg-config python3-venv python3-pip pipx ffmpeg sqlite3 unzip podman
```

When it finishes, verify Podman without using `sudo`:

```bash
podman info
```

**Expected result:** A multi-section information report. A warning about a first-time configuration is usually fine. A password prompt is not expected for the `podman info` check.

Podman is available from Ubuntu’s official repositories and is the selected container runtime for the future OpenS FULL profile; it is only a preparation tool on this LITE host. [4]

**Continue when:** The package command and `podman info` finish without a fatal error.

---

## Card 16 — Create private local folders for OpenS

**Reader says:** “Open Terminal. Create private folders for future installer files, models, data, backups, and logs. These folders do not install OpenS. They only keep the future installation organized.”

**You do:** Run these commands:

```bash
mkdir -p "$HOME/OpenS/installers" "$HOME/OpenS/models" "$HOME/OpenS/data" "$HOME/OpenS/backups" "$HOME/OpenS/logs"
chmod 700 "$HOME/OpenS" "$HOME/OpenS/installers" "$HOME/OpenS/models" "$HOME/OpenS/data" "$HOME/OpenS/backups" "$HOME/OpenS/logs"
ls -ld "$HOME/OpenS" "$HOME/OpenS"/*
```

**Expected result:** A list of six folders. Their permissions should begin with `drwx------`.

**Continue when:** You see the folders.

---

## Card 17 — Turn on a basic inbound firewall

**Reader says:** “This machine is a local workstation. We will deny unsolicited incoming network connections and allow normal outgoing internet connections. Do this only while you are physically at the computer, not while remotely connected through SSH.”

**You do:** Run these commands:

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
sudo ufw status verbose
```

**Expected result:** The last command shows `Status: active`, `Default: deny (incoming)`, and `allow (outgoing)`.

**Do not do:** Do not open web, database, model-server, or container ports to the internet. OpenS is designed for no public inference or data-service ports by default.

**Continue when:** UFW shows active with incoming connections denied.

---

## Card 18 — Make the first Ubuntu backup

**Reader says:** “Connect a backup drive that is not the Ubuntu boot drive. Open the Backups app from the Applications menu. Select the external drive. Turn on encryption for the backup. Run one backup now. When it finishes, use Restore in the same app to browse the backup. You do not need to restore anything; the goal is to prove the backup is readable.”

**You do:** Create an encrypted Ubuntu backup to an external drive.

**Continue when:** You can browse the backup contents and then safely unplug the backup drive.

---

## Card 19 — Copy and verify the rebuilt Ubuntu Glove source

**Reader says:** “Reconnect the external backup drive. In Files, copy `ubuntu-glove-rebuilt-0.2.0-alpha.zip` and `ubuntu-glove-rebuilt-0.2.0-alpha.sha256` into Home, OpenS, installers. Eject the backup drive again. Open Terminal. The first command must say OK before you continue.”

**You do:** Run these commands one at a time:

```bash
cd "$HOME/OpenS/installers"
sha256sum -c ubuntu-glove-rebuilt-0.2.0-alpha.sha256
unzip -q ubuntu-glove-rebuilt-0.2.0-alpha.zip
cd ubuntu-glove-rebuilt && chmod +x scripts/install_stack.sh scripts/ubuntu-glove scripts/build_deb.sh scripts/create_source_bundle.sh debian/rules
```

**Expected result:** The checksum command says `OK` and the project folder is `$HOME/OpenS/installers/ubuntu-glove-rebuilt`.

**Continue when:** The folder exists and the command finishes without an error.

---

## Card 20 — Install Ubuntu Glove’s GNOME dependencies

**Reader says:** “Ubuntu Glove needs Ubuntu GNOME packages for GTK, accessibility, the optional overlay, indicator, and screenshots. These are operating-system packages, not pip packages. Run the commands exactly as written.”

**You do:** Run these commands one line at a time:

```bash
cd "$HOME/OpenS/installers/ubuntu-glove-rebuilt"
sudo apt update
sudo apt install -y python3 python3-gi python3-gi-cairo python3-pyatspi at-spi2-core gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-ayatanaappindicator3-0.1 gir1.2-gtk4layershell-1.0 gnome-screenshot
python3 main.py --check-data
```

**Expected result:** The last command prints JSON with `commands: 2`, categories `Networking` and `System Maintenance`, `onboarding_rules: 2`, and `model_routes: 0`.

Ubuntu 26.04 carries the required GTK4 layer-shell and AT-SPI Python packages. [6] [7]

**Continue when:** The JSON validation prints the expected record counts.

---

## Card 21 — Smoke-test Ubuntu Glove without the tray service

**Reader says:** “We will test the overlay first, without installing a background service. Run the command. A small blue U should appear near the upper-left desktop. Click it. Test Commands and Save note. Do not test Read screen yet. Close the app with Control C in Terminal.”

**You do:** Run:

```bash
cd "$HOME/OpenS/installers/ubuntu-glove-rebuilt"
python3 main.py --no-tray
```

Test only these local features:

1. Click the blue **U** avatar.
2. Select **Commands**, choose a command, and confirm it is only placed on the clipboard. Do not run it unless you understand it.
3. Enter a harmless note such as `Test note` and select **Save note**.
4. Press `Ctrl+C` in the Terminal to close the test.

**Continue when:** The avatar appears, the command palette opens, and a note saves without an error.

---

## Card 22 — Enable desktop accessibility support

**Reader says:** “Ubuntu Glove uses the normal GNOME accessibility service for window titles, focus information, notes, and context tips. This does not turn on microphone or camera access. First check its state. If it says false, enable it for this user only. Do not use sudo.”

**You do:** Run:

```bash
gsettings get org.gnome.desktop.interface toolkit-accessibility
```

If it prints `false`, then run:

```bash
gsettings set org.gnome.desktop.interface toolkit-accessibility true
systemctl --user restart at-spi-dbus-bus.service 2>/dev/null || true
```

If context tips still do not appear later, log out and log back in once.

**Continue when:** The setting is `true`, or you have logged back in after enabling it.

---

## Card 23 — Install Ubuntu Glove for your user account

**Reader says:** “This installs Ubuntu Glove only for the logged-in desktop user. It copies application code under your home folder, preserves notes and settings during future updates, creates a launcher, and starts a user-level service. There is no system-wide option. Do not run this through SSH.”

**You do:** Run these commands:

```bash
cd "$HOME/OpenS/installers/ubuntu-glove-rebuilt"
bash scripts/install_stack.sh --enable
systemctl --user status ubuntu-glove.service --no-pager
```

**Expected result:** The service status includes `active (running)`. A small Ubuntu Glove avatar and, on supported GNOME configurations, a top-bar indicator appear.

**If the service shows a display, Wayland, or session-bus error:** Run `systemctl --user stop ubuntu-glove.service`, then start it manually from the GNOME Terminal with `~/.local/bin/ubuntu-glove --activate`. Do not keep retrying a broken service.

**Continue when:** The overlay starts or the manual launch works.

---

## Card 24 — Optional: enable Bash command staging

**Reader says:** “This is optional. It lets Control Space in Bash open the Ubuntu Glove command palette. The chosen command is inserted into the current prompt for your review. It is not executed automatically.”

**You do:** Run these commands only if you want the feature:

```bash
if ! grep -qxF 'source "$HOME/.local/share/ubuntu-glove/app/scripts/bashrc_hook.sh"' "$HOME/.bashrc"; then
  printf '\nsource "$HOME/.local/share/ubuntu-glove/app/scripts/bashrc_hook.sh"\n' >> "$HOME/.bashrc"
fi
source "$HOME/.bashrc"
```

Open a fresh Terminal, press `Ctrl+Space`, select a command, and verify that it appears in the prompt but does not run until you review it and press Enter.

**Continue when:** The palette opens or you deliberately skip this optional feature.

---

## Card 25 — Keep LLM and screen reading off for the first pilot

**Reader says:** “The rebuilt app works locally without a model. Its model lock is intentionally empty because no validated local model artifact was supplied. Do not configure an endpoint or use Read screen during the first pilot. This keeps testing limited to local notes, tips, overlay behavior, and command staging.”

**You do:** Do not create `~/.config/ubuntu-glove/settings.json` yet. Do not select **Read screen** yet.

When OpenS LITE supplies a validated local `llama.cpp` model gateway, this app can use only its OpenAI-compatible `127.0.0.1` or `[::1]` endpoint. A reviewed model route with an exact revision and SHA-256 must first exist in `data/models.lock.json`. `llama.cpp` supports a local OpenAI-compatible server and GPU acceleration, but it is not part of this alpha archive. [5]

**Continue when:** Ubuntu Glove works with local features only.

---

## Card 26 — Voice and Presence: not installed by this archive

**Reader says:** “Ubuntu Glove does not add the OpenS Presence and Voice module. It has no microphone, speech recognition, text-to-speech, or voice-command capability. Leave that work uninstalled. The future OpenS module must be a separate, tested local chain with visible mic and camera state, a kill switch, no identity tracking, no raw audio or video retention by default, and no cloud processing by default.”

**You do:** Do not install OpenVINO, Whisper, WebRTC VAD, Qwen TTS, or a wake-word package from random instructions.

If and only if a future signed OpenS LITE release presents the tested feature, its approved local chain is:

```text
Camera → OpenVINO person-detection-0203 → local presence state
Microphone → WebRTC VAD → Whisper base / faster-whisper
Text → Qwen3-4B / llama.cpp → Qwen3-TTS CustomVoice → local speaker
```

---

## Card 27 — Final alpha-pilot checklist

**Reader says:** “Read this list. If every relevant line is true, the Ubuntu host and Ubuntu Glove alpha pilot are ready. Do not call this a completed OpenS LITE production deployment.”

**You do:** Check each item:

- [ ] Windows is gone from the target drive and Ubuntu boots after the USB is removed.
- [ ] You know the disk-encryption passphrase and Ubuntu login password, and they are stored safely off the PC.
- [ ] `sudo apt full-upgrade -y` completed and the PC rebooted successfully.
- [ ] If this PC has NVIDIA graphics, `nvidia-smi` shows the expected GPU.
- [ ] Network, keyboard, display, camera, microphone, and speakers work in Ubuntu.
- [ ] `podman info` works without `sudo`.
- [ ] `~/OpenS` and its private subfolders exist.
- [ ] UFW is active with incoming connections denied.
- [ ] You have made and browsed at least one encrypted external backup.
- [ ] `python3 main.py --check-data` passed before installation.
- [ ] Ubuntu Glove’s local overlay, command palette, and note save test passed.
- [ ] The rebuilt source archive checksum reported `OK` before extraction.
- [ ] No LLM endpoint, screen reading, microphone feature, random model, public model server, or FULL stack is installed by hand.

If every relevant line is checked, say: **“Ubuntu LITE host and Ubuntu Glove alpha pilot complete.”**

---

# Quick problem cards

## Problem A — The USB will not boot

1. Restart.
2. Open the temporary boot menu again.
3. Choose the entry that starts with **UEFI** and has the USB name.
4. If there is no USB entry, recreate the USB in Rufus using **GPT** and **UEFI (non CSM)**, then try a different USB port.

## Problem B — Ubuntu says Intel RST is enabled

Stop. Do **not** erase the drive yet. Ubuntu cannot proceed normally while Intel Rapid Storage Technology is controlling the Windows drive. The official Ubuntu documentation has a specific Windows-to-AHCI procedure. Read it from a second device and back up first: <https://ubuntu.com/desktop/docs/en/latest/how-to/reconfigure-windows-to-use-ahci/>. [2]

## Problem C — I accidentally selected the wrong drive before clicking Install

Click **Back** or **Cancel**. No damage has happened until the final installation confirmation starts writing the disk. Disconnect the incorrect drive and start again.

## Problem D — NVIDIA does not work after Ubuntu installs

1. Make sure Ubuntu is fully updated.
2. Open **Additional Drivers**.
3. Select the NVIDIA option marked **recommended**.
4. Apply changes and reboot.
5. Run `nvidia-smi` again.

Do not install a `.run` file from a random search result. Do not mix multiple NVIDIA driver sources.

## Problem E — I forgot the disk encryption passphrase

There is no safe bypass. Ubuntu’s disk encryption is intentionally unrecoverable without the passphrase. You must restore from a backup or reinstall the OS. [2]

## Problem F — Ubuntu Glove will not start

First confirm that you are inside the logged-in Ubuntu GNOME desktop session, not SSH. Then run:

```bash
cd "$HOME/OpenS/installers/ubuntu-glove-rebuilt"
python3 main.py --check-data
python3 main.py --no-tray
```

If the error says `No module named gi`, repeat Card 20. If the avatar appears as a regular window, install `gir1.2-gtk4layershell-1.0`; do not try to bypass GNOME/Wayland security boundaries. If the user service fails with a display, Wayland, or session-bus error, stop it and launch `~/.local/bin/ubuntu-glove --activate` from a visible GNOME Terminal.

---

## References

[1]: https://documentation.ubuntu.com/release-notes/26.04/ "Ubuntu 26.04 LTS release notes"

[2]: https://ubuntu.com/desktop/docs/en/latest/tutorial/install-ubuntu-desktop/ "Install Ubuntu Desktop"

[3]: https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/latest/ubuntu.html "NVIDIA Driver Installation Guide for Ubuntu"

[4]: https://podman.io/docs/installation "Podman installation instructions"

[5]: https://github.com/ggml-org/llama.cpp "llama.cpp local inference project"

[6]: https://launchpad.net/ubuntu/resolute/armhf/gir1.2-gtk4layershell-1.0 "Ubuntu 26.04 GTK4 layer shell introspection package"

[7]: https://packages.ubuntu.com/resolute/python3-pyatspi "Ubuntu 26.04 Python AT-SPI bindings"
