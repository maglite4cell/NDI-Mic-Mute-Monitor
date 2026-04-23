# NDI Shure Monitor

**NDI Shure Monitor** is a standalone service and live visual dashboard that monitors wireless microphone mute statuses and broadcasts them across your network as an NDI video feed — ready to overlay in OBS, vMix, or any NDI-capable video switcher.

[![CI](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/actions/workflows/ci.yml)
[![Build & Release](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/actions/workflows/build-release.yml/badge.svg)](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/actions/workflows/build-release.yml)

---

## Why NDI Shure Monitor?

Running a live broadcast without a fast, reliable mic status overlay is a liability. This tool bridges the gap between your wireless hardware and your video production stack — no additional hardware or costly software bridges required.

- 🎙️ **Real-time mute status** from Shure receivers over TCP
- 🎛️ **Behringer X32 & WING** mute tracking via OSC subscription
- 📡 **NDI broadcast output** — ingest directly into OBS, vMix, or hardware switchers
- 🖥️ **Web dashboard** — configure everything at `http://localhost:8001`, live, no restart needed
- ⚡ **Lightweight** — runs headlessly, no GPU required for the NDI feed

---

## Quick Start

### 1. Download a Pre-built Binary

Download the latest `.app` (macOS) or `.exe` (Windows) from the [GitHub Releases](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/releases) page.

!!! warning "macOS Gatekeeper"
    Because this app is not notarized, macOS may block it. Run this once in Terminal:
    ```bash
    xattr -cr "/Applications/NDI Shure Monitor.app"
    ```
    Then open normally.

### 2. Install the NDI Runtime

The NDI Runtime must be installed on any machine that will **send or receive** the NDI feed.

> [Download NDI Tools](https://ndi.video/tools/) from ndi.video — it's free.

### 3. Configure Your Hardware

Open `http://localhost:8001` in your browser. Add your Shure receiver's IP address and configure channel slots. That's it — the NDI feed starts automatically.

---

## Running from Source

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
git clone https://github.com/maglite4cell/NDI-Mic-Mute-Monitor.git
cd NDI-Mic-Mute-Monitor

# Install dependencies
uv sync

# Install with NDI output support (requires NDI SDK installed first)
uv sync --all-extras

# Run
uv run python main.py
```

!!! note
    Without the NDI SDK, the app runs in **mock mode** — the dashboard and Shure/OSC monitors work fully, but no NDI feed is broadcast.

---

## Architecture

```
┌──────────────────┐    TCP/2202    ┌─────────────────────┐
│  Shure Receiver  │ ─────────────> │  GlobalShureManager  │
└──────────────────┘                └──────────┬──────────┘
                                               │
┌──────────────────┐    OSC/UDP     ┌──────────▼──────────┐
│  Behringer X32   │ ─────────────> │  GlobalOscManager   │
│  Behringer WING  │                │  (x32 / wing)        │
└──────────────────┘                └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │     State Manager    │
                                    └──────────┬──────────┘
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        │                      │                       │
             ┌──────────▼──────┐    ┌──────────▼──────┐   ┌──────────▼──────┐
             │   NDI Worker    │    │   Web Dashboard  │   │  config.json     │
             │  (PyGame/NDI)   │    │  (FastAPI/8001)  │   │  (persistence)   │
             └─────────────────┘    └─────────────────┘   └─────────────────┘
```

---

## Supported Hardware

| Protocol | Hardware | Notes |
|---|---|---|
| Shure TCP | QLX-D, ULX-D, SLX-D, Axient Digital | Port 2202 |
| OSC | Behringer X32 / X32 Rack / X32 Compact | Port 10023 |
| OSC | Behringer WING / WING Rack | Port 2223 |

See the [Protocols](protocols.md) page for full compatibility details.

---

## Support This Project

💖 If this has saved your service, broadcast, or live gig, consider sponsoring:

**[Sponsor @maglite4cell on GitHub Sponsors](https://github.com/sponsors/maglite4cell)**

---

## License

MIT License. See [LICENSE](https://github.com/maglite4cell/NDI-Mic-Mute-Monitor/blob/main/LICENSE).  
NDI® is a registered trademark of Vizrt Group. Bundled NDI runtime libraries are subject to the [NDI SDK License Agreement](https://ndi.video/legal/).
