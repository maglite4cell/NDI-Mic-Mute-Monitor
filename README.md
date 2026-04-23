# NDI Shure Monitor

[![CI](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/actions/workflows/ci.yml)
[![Build & Release](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/actions/workflows/build-release.yml/badge.svg)](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/actions/workflows/build-release.yml)

A standalone service and visual dashboard that monitors Shure wireless microphones and broadcasts their statuses as an NDI video feed.

## Overview
This application connects directly to your Shure wireless microphone receivers to retrieve their statuses in real-time (Link OK, Muted, Channel Name). It renders this information visually using PyGame and broadcasts it across your local network via NDI, allowing modern video switchers (like OBS, vMix, or hardware switchers) to directly ingest and overlay the feed.

It also provides a FastAPI-driven web dashboard (`http://localhost:8001`) to configure layouts, hide/show layers, and toggle network configurations on the fly without needing to restart the primary engine.

## Architecture
- **Shure Client:** TCP engine that periodically retrieves live RF and Mute statistics.
- **NDI Worker:** Cross-platform renderer bridging Python, PyGame, and `ndi-python` into a single broadcast output.
- **Web Dashboard:** FastAPI singleton instance allowing instant configuration adjustments via a mobile-friendly frontend.
- **State Manager:** Thread-safe state arbiter persisting configuration layers.

---

## Prerequisites

### 1. NDI Runtime (Required to receive the NDI output)
The NDI Runtime must be installed on any machine that will **receive** the NDI video feed (your switcher/OBS machine). It is **free** and available from NDI's official site:

> **Download:** https://ndi.video/tools/ → *NDI Tools* (includes the runtime)

The runtime is required on the machine **running this app** as well to broadcast the NDI source.

### 2. NDI SDK (Required only to build from source)
If you are running from source (not using a pre-built binary), you must also install the **NDI SDK** before the `ndi-python` package can be compiled.

> **Download:** https://ndi.video/tools/ndi-sdk/

- **macOS:** Install the `.pkg` file. The SDK installs to `/Library/NDI SDK for Apple/`.
- **Windows:** Run the `.exe` installer.

Once the SDK is installed, install `ndi-python` via the `ndi` optional extra (see Setup below).

---

## Setup and Installation

### Pre-built Binaries (Recommended)
Download the latest `.app` (macOS) or `.exe` (Windows) from the [Releases](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/releases) page. No Python or NDI SDK required — just the NDI Runtime.

### Running from Source using `uv`
This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Clone the repository
git clone https://github.com/maglite4cell/NDI-Mic-Mute-Monitor.git
cd NDI-Mic-Mute-Monitor

# Install core dependencies
uv sync

# Install with NDI support (requires NDI SDK installed first — see Prerequisites)
uv sync --all-extras

# Run the app
uv run python main.py
```

> **Note:** If the NDI SDK is not installed, the app will still start in **mock mode** — the web dashboard and Shure client work normally, but no NDI output is broadcast.

### Modifying Configuration
Navigate to `http://localhost:8001` in your browser. From here you can configure:
- Your Shure receiver IP addresses and ports.
- Custom naming and toggle "Sync Receiver Name".
- Enable/Disable specific channel slots.
- Choose between Fixed and Spaced visual layout modes.

All configurations are persisted in `config.json` (next to the app when running from source, or in your user app data directory when running a bundled binary).

- **macOS (bundled):** `~/Library/Application Support/NDI Shure Monitor/config.json`
- **Windows (bundled):** `%APPDATA%\NDI Shure Monitor\config.json`

---

## Generating Executables
This repository is configured to auto-build Mac `.app` and Windows `.exe` binary bundles via GitHub Actions on every newly tagged Release. You can also build locally:
```bash
uv run --with pyinstaller pyinstaller NDI_Shure_Monitor.spec
```

---

## Support / Limitations
- Relies on Shure Standard Control Strings via TCP (typically port 2202). Tested with AD, ULXD, QLXD, and SLXD series receivers.
- Python 3.9 is required due to `ndi-python` pre-built wheel limitations on macOS.
- NDI output is broadcast as a transparent BGRA overlay suitable for compositing in vMix, OBS, or hardware NDI switchers.

## License
This project is provided under the MIT License. See [LICENSE](LICENSE) for details.

This software uses NDI® technology. NDI® is a registered trademark of Vizrt Group.
NDI runtime libraries bundled in binary releases are subject to the [NDI SDK License Agreement](https://ndi.video/legal/).
