# Configuration

All configuration is stored in `config.json` and is fully editable through the web dashboard at `http://localhost:8001`. Changes take effect immediately — no restart required.

---

## Config File Location

| Environment | Path |
|---|---|
| Running from source | `config.json` (next to `main.py`) |
| macOS bundled app | `~/Library/Application Support/NDI Shure Monitor/config.json` |
| Windows bundled app | `%APPDATA%\NDI Shure Monitor\config.json` |

---

## Global Display Settings

These control what the NDI output and web preview show.

| Key | Type | Default | Description |
|---|---|---|---|
| `show_preview` | bool | `true` | Show the live preview on the web dashboard |
| `show_leds` | bool | `true` | Show status LED indicators on the NDI output |
| `show_names` | bool | `true` | Show channel name labels |
| `show_battery` | bool | `false` | Show battery percentage indicators |
| `layout_mode` | string | `"fixed"` | `"fixed"` keeps slots in place; `"spaced"` distributes active channels evenly |

---

## Connections

The `connections` block holds IP and port for each supported hardware type.

```json
{
  "connections": {
    "shure": {
      "ip": "192.168.1.50",
      "port": 2202
    },
    "x32": {
      "ip": "192.168.1.100",
      "port": 10023
    },
    "wing": {
      "ip": "192.168.1.101",
      "port": 2223
    }
  }
}
```

!!! tip
    Set the IP to `127.0.0.1` to disable a connection. The monitor manager will skip connecting to loopback addresses.

---

## LED Channel Slots (`leds`)

Each entry in the `leds` array defines one channel slot on the NDI output.

```json
{
  "id": 0,
  "name": "Pulpit",
  "enabled": true,
  "interval": 500,
  "monitor_type": "shure",
  "target": "1",
  "use_receiver_name": true,
  "use_live_status": true
}
```

### LED Fields

| Field | Type | Description |
|---|---|---|
| `id` | int | Unique slot identifier (0-based) |
| `name` | string | Display label for this slot |
| `enabled` | bool | Whether this slot is visible on the NDI output |
| `interval` | int | Blink interval in milliseconds when status is MUTE |
| `monitor_type` | string | Hardware source: `"shure"`, `"x32"`, or `"wing"` |
| `target` | string | What to monitor (see below) |
| `use_receiver_name` | bool | Auto-populate name from the receiver (Shure only) |
| `use_live_status` | bool | Update status from live hardware data |
| `status` | string | Override status: `"OK"` or `"MUTE"` (used when `use_live_status` is `false`) |

### `target` Values by Monitor Type

=== "Shure"
    Set `target` to the **channel number** on the receiver (as a string):
    ```json
    "monitor_type": "shure",
    "target": "1"
    ```
    Channel numbers match the physical channel inputs on your Shure receiver (1–4 for most models).

=== "Behringer X32"
    Set `target` to the **full OSC address** for the channel's mute/on state:
    ```json
    "monitor_type": "x32",
    "target": "/ch/01/mix/on"
    ```
    On X32, `/mix/on` value of `1` = active (unmuted), `0` = muted.

=== "Behringer WING"
    Set `target` to the **full OSC address** for the channel mute:
    ```json
    "monitor_type": "wing",
    "target": "/ch/1/mute"
    ```
    On WING, `/mute` value of `1` = muted, `0` = active.

---

## Example Full Config

```json
{
  "show_preview": true,
  "show_leds": true,
  "show_names": true,
  "show_battery": false,
  "layout_mode": "fixed",
  "connections": {
    "shure": { "ip": "192.168.1.50", "port": 2202 },
    "x32":   { "ip": "192.168.1.100", "port": 10023 },
    "wing":  { "ip": "192.168.1.101", "port": 2223 }
  },
  "leds": [
    {
      "id": 0, "name": "Pulpit", "enabled": true, "interval": 500,
      "monitor_type": "shure", "target": "1",
      "use_receiver_name": true, "use_live_status": true
    },
    {
      "id": 1, "name": "Lav 1", "enabled": true, "interval": 500,
      "monitor_type": "x32", "target": "/ch/01/mix/on",
      "use_receiver_name": false, "use_live_status": true
    },
    {
      "id": 2, "name": "Lav 2", "enabled": true, "interval": 500,
      "monitor_type": "wing", "target": "/ch/2/mute",
      "use_receiver_name": false, "use_live_status": true
    }
  ]
}
```
