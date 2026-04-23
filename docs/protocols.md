# Protocols

NDI Shure Monitor connects to three hardware protocols simultaneously via its `GlobalMonitorManager`. Each protocol runs on its own persistent thread and reports status changes directly to the shared state.

---

## Shure Standard Control Strings (TCP)

**Connection:** TCP, port **2202**  
**Manager:** `GlobalShureManager`

Shure's ASCII-based TCP protocol is supported across all networked wireless product lines. The app opens a persistent TCP connection and uses a combination of real-time **push notifications** from the receiver (sent automatically when values change) and a **30-second periodic sync** as a safety net.

### Supported Commands

| Command | Direction | Description |
|---|---|---|
| `GET {ch} CHAN_NAME` | → Receiver | Request channel name |
| `GET {ch} TX_MUTE_STATUS` | → Receiver | Request transmitter mute state |
| `GET {ch} BATT_CHARGE` | → Receiver | Request battery percentage |
| `GET {ch} RF_ANTENNA` | → Receiver | Request RF antenna status |
| `REP {ch} CHAN_NAME {value}` | ← Receiver | Channel name update |
| `REP {ch} TX_MUTE_STATUS {OFF\|ON}` | ← Receiver | Mute state (`OFF` = active, `ON` = muted) |
| `REP {ch} BATT_CHARGE {0-100\|255}` | ← Receiver | Battery % (`255` = no transmitter) |
| `REP {ch} RF_ANTENNA {A\|B\|XX}` | ← Receiver | RF signal (`XX` = no signal) |

### Status Mapping

| Receiver Report | LED Status |
|---|---|
| `TX_MUTE_STATUS OFF` | ✅ OK |
| `TX_MUTE_STATUS ON` | 🔴 MUTE |
| `RF_ANTENNA XX` | 🔴 MUTE (no RF) |
| `BATT_CHARGE 255` | Battery: None |

### Tested Hardware

| Model | Role | Status |
|---|---|---|
| QLXD4 | Receiver | ✅ Confirmed |
| QLXD2 | Handheld TX | ✅ Confirmed |

### Expected Compatible Hardware

| Series | Receiver Models |
|---|---|
| **QLX-D** | QLXD4, QLXD4D |
| **ULX-D** | ULXD4, ULXD4D, ULXD4Q |
| **SLX-D** | SLXD4, SLXD4D ⚠️ |
| **Axient Digital** | AD4D, ADX4, ADX4D |

!!! warning "SLX-D Users"
    Third-party TCP control is **blocked by default** on SLX-D receivers. Enable it via:  
    Front panel → **Advanced Settings** → **Controller Access** → **Allow**

### Protocol Documentation

- [Shure Command Strings Hub](https://pubs.shure.com/command-strings)
- [QLXD Command Strings](https://pubs.shure.com/command-strings/QLXD/)
- [ULXD Command Strings](https://pubs.shure.com/command-strings/ULXD/)
- [SLXD Command Strings](https://pubs.shure.com/command-strings/SLXD/)
- [Axient Digital Command Strings](https://pubs.shure.com/command-strings/AD/)

---

## Behringer X32 (OSC)

**Connection:** OSC over UDP, port **10023**  
**Manager:** `GlobalOscManager` (type: `x32`)

The app subscribes to mute/on states on the X32 using the `/xremote` keep-alive mechanism. It binds an OSC listener on a random local UDP port and sends `/xremote` every 8 seconds (the X32 subscription expires after 10 seconds).

### Mute Logic

On X32, `/ch/XX/mix/on`:

| OSC Value | LED Status |
|---|---|
| `1` | ✅ OK (channel active) |
| `0` | 🔴 MUTE |

### Common OSC Addresses

| Address | Description |
|---|---|
| `/ch/01/mix/on` | Channel 1 on/mute state |
| `/ch/16/mix/on` | Channel 16 on/mute state |
| `/bus/01/mix/on` | Mix Bus 1 on/mute state |

!!! tip
    Use the exact OSC address format as the `target` in your LED config. Pad channel numbers with a leading zero: `/ch/01/`, `/ch/02/`, etc.

---

## Behringer WING (OSC)

**Connection:** OSC over UDP, port **2223**  
**Manager:** `GlobalOscManager` (type: `wing`)

The WING uses the same keep-alive subscription mechanism as the X32 (`/xremote` every 8 seconds), but its mute logic is **inverted**.

### Mute Logic

On WING, `/ch/X/mute`:

| OSC Value | LED Status |
|---|---|
| `0` | ✅ OK (unmuted) |
| `1` | 🔴 MUTE |

### Common OSC Addresses

| Address | Description |
|---|---|
| `/ch/1/mute` | Channel 1 mute state |
| `/ch/16/mute` | Channel 16 mute state |
| `/aux/1/mute` | Aux 1 mute state |

!!! tip
    WING channel numbers are **not** zero-padded: `/ch/1/`, `/ch/2/`, etc.

---

## Protocol Comparison

| Feature | Shure TCP | X32 OSC | WING OSC |
|---|---|---|---|
| Transport | TCP | UDP | UDP |
| Default Port | 2202 | 10023 | 2223 |
| Push Updates | ✅ Yes | ✅ Yes (via subscription) | ✅ Yes (via subscription) |
| Keep-alive | 30s periodic sync | `/xremote` every 8s | `/xremote` every 8s |
| Muted value | `TX_MUTE_STATUS ON` | `/mix/on = 0` | `/mute = 1` |
| Active value | `TX_MUTE_STATUS OFF` | `/mix/on = 1` | `/mute = 0` |
| Battery info | ✅ Yes | ❌ No | ❌ No |
| Channel names | ✅ Yes (receiver name sync) | ❌ No | ❌ No |
