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

## Setup and Installation

### Running from source using `uv`
This project relies on [uv](https://github.com/astral-sh/uv) by Astral for rapid dependency management. Ensure it is installed on your system.

```bash
# Clone the repository
git clone https://github.com/maglite4cell/NDI-Mic-Mute-Monitor.git
cd NDI-Shure-Monitor

# Sync dependencies and run
uv sync
uv run python main.py
```

### Modifying Configuration
Navigate to `http://localhost:8001` in your browser. From here you can configure:
- Your Shure receiver IP addresses / ports.
- Custom naming and toggle "Sync Receiver Name".
- Enable/Disable specific LED slots.
- Choose between Fixed and Spaced visual layout modes.

All configurations are persisted in `config.json`.

## Generating Executables
This repository is configured to auto-build Mac `.app` and Windows `.exe` binary bundles via GitHub Actions on every newly tagged Release. You can also build it locally:
```bash
uv run --with pyinstaller pyinstaller NDI_Shure_Monitor.spec
```

## Support / Limitations
- Relies on Shure Standard Control Strings via TCP (typically port 2202). Tested with AD, ULXD, QLXD and SLXD series receivers.
- Python 3.9 is required due to `ndi-python` pre-built wheel limitations on macOS.

## License
Provided under the MIT License.
