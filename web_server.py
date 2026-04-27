from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import threading
from state import state, logger, LOG_FILE
import os
import logging

app = FastAPI()

# Input Models
class LedUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    enabled: Optional[bool] = None
    interval: Optional[int] = None
    monitor_type: Optional[str] = None
    target: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    use_receiver_name: Optional[bool] = None
    use_live_status: Optional[bool] = None

class ConnectionConfig(BaseModel):
    ip: str
    port: int

class ConfigUpdate(BaseModel):
    leds: List[LedUpdate]
    connections: Optional[Dict[str, ConnectionConfig]] = None
    show_preview: Optional[bool] = None
    show_leds: Optional[bool] = None
    show_names: Optional[bool] = None
    show_battery: Optional[bool] = None
    layout_mode: Optional[str] = None
    enable_debug_logging: Optional[bool] = None

class ChannelStatusUpdate(BaseModel):
    status: Optional[str] = None
    battery: Optional[int] = None

# API Endpoints
@app.get("/api/config")
def get_config():
    return state.config

@app.post("/api/config")
def update_config(update: ConfigUpdate):
    for item in update.leds:
        state.update_led(item.id, item.model_dump(exclude_unset=True))
    
    with state._lock:
        if update.connections is not None:
            if "connections" not in state.config:
                state.config["connections"] = {}
            for k, v in update.connections.items():
                if k in state.config["connections"]:
                    state.config["connections"][k]["ip"] = v.ip
                    state.config["connections"][k]["port"] = v.port
        if update.show_preview is not None:
            state.config["show_preview"] = update.show_preview
        if update.show_leds is not None:
            state.config["show_leds"] = update.show_leds
        if update.show_names is not None:
            state.config["show_names"] = update.show_names
        if update.show_battery is not None:
            state.config["show_battery"] = update.show_battery
        if update.layout_mode is not None:
            state.config["layout_mode"] = update.layout_mode
        if update.enable_debug_logging is not None:
            state.config["enable_debug_logging"] = update.enable_debug_logging
            if update.enable_debug_logging:
                logger.setLevel(logging.DEBUG)
            else:
                logger.setLevel(logging.INFO)
        
    state.save_config()
        
    return {"status": "ok", "config": state.config}

@app.post("/api/channel/{id}/status")
def update_channel_status(id: int, update: ChannelStatusUpdate):
    updates = {}
    if update.status is not None:
        updates['status'] = update.status
    if update.battery is not None:
        updates['battery'] = update.battery
        
    if updates:
        state.update_single_led(id, **updates)
        
    return {"status": "ok"}

@app.get("/api/logs/download")
def download_logs():
    if os.path.exists(LOG_FILE):
        return FileResponse(LOG_FILE, filename="debug.log")
    return {"status": "error", "message": "Log file not found"}

# HTML Dashboard
dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>NDI Shure Monitor</title>
    <style>
        :root {
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --text-color: #e0e0e0;
            --accent: #bb86fc;
            --success: #03dac6;
            --danger: #cf6679;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            -webkit-tap-highlight-color: transparent;
        }
        h1 { text-align: center; font-weight: 300; margin-bottom: 20px; }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }

        .led-card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        .led-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .led-id { font-size: 0.8em; opacity: 0.7; }
        
        input[type="text"], input[type="number"], select {
            background: #2c2c2c;
            border: 1px solid #333;
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-size: 16px;
            width: 100%;
            box-sizing: border-box;
        }

        .controls {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-top: 10px;
        }

        label { font-size: 0.9em; opacity: 0.8; display: block; margin-bottom: 5px; }

        .switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: #333;
            transition: .4s;
            border-radius: 34px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider { background-color: var(--success); }
        input:checked + .slider:before { transform: translateX(26px); }

        .btn-save {
            background-color: var(--accent);
            color: black;
            border: none;
            padding: 15px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.1em;
            cursor: pointer;
            width: 100%;
            margin-top: 30px;
            position: sticky;
            bottom: 20px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            z-index: 100;
        }
        .btn-save:active { transform: scale(0.98); }

    </style>
</head>
<body>

    <h1>NDI Monitor Config</h1>

    <div id="app" class="container">
        <!-- Cards injected by JS -->
    </div>

    <button class="btn-save" onclick="saveConfig()">Save All Changes</button>

    <script>
        let currentState = { leds: [], connections: {} };

        function escHtml(str) {
            return String(str ?? '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }

        async function fetchConfig() {
            const res = await fetch('/api/config');
            const data = await res.json();
            currentState = data;
            if (!currentState.connections) currentState.connections = {};
            render();
        }

        function updateConnection(type, key, value) {
            if (!currentState.connections[type]) currentState.connections[type] = {};
            currentState.connections[type][key] = value;
        }

        function getTargetSelector(led) {
            const type = led.monitor_type;
            const current = led.target || '';
            
            if (type === 'api') {
                return `<div style="margin-top: 10px;">
                    <label style="color: #aaa; font-size: 0.8em;">Endpoint</label>
                    <code style="background: #000; padding: 8px; border-radius: 4px; display: block; margin-top: 5px; color: var(--success);">POST /api/channel/${led.id}/status</code>
                </div>`;
            }
            
            if (type === 'shure' || type === 'sennheiser') {
                return `
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <div style="flex: 2;">
                        <label>Receiver IP</label>
                        <input type="text" value="${escHtml(led.ip)}" oninput="updateState(${led.id}, 'ip', this.value)" placeholder="192.168.1.XX">
                    </div>
                    <div style="flex: 1;">
                        <label>Port</label>
                        <input type="number" value="${led.port}" oninput="updateState(${led.id}, 'port', parseInt(this.value))">
                    </div>
                </div>
                <div style="margin-top: 10px;">
                    <label>Receiver Channel</label>
                    <input type="text" value="${escHtml(current)}" oninput="updateState(${led.id}, 'target', this.value)" placeholder="1, 2, 3...">
                </div>`;
            }
            
            if (type === 'x32' || type === 'wing') {
                let options = [];
                if (type === 'x32') {
                    for(let i=1; i<=32; i++) options.push({val: `/ch/${i.toString().padStart(2,'0')}/mix/on`, label: `Channel ${i}`});
                    for(let i=1; i<=8; i++) options.push({val: `/auxin/${i.toString().padStart(2,'0')}/mix/on`, label: `Aux In ${i}`});
                    for(let i=1; i<=8; i++) options.push({val: `/fxrtn/${i.toString().padStart(2,'0')}/mix/on`, label: `FX Return ${i}`});
                    for(let i=1; i<=16; i++) options.push({val: `/bus/${i.toString().padStart(2,'0')}/mix/on`, label: `MixBus ${i}`});
                    for(let i=1; i<=6; i++) options.push({val: `/mtx/${i.toString().padStart(2,'0')}/mix/on`, label: `Matrix ${i}`});
                    options.push({val: '/main/st/mix/on', label: 'Main LR'});
                } else {
                    for(let i=1; i<=40; i++) options.push({val: `/ch/${i}/mute`, label: `Channel ${i}`});
                    for(let i=1; i<=8; i++) options.push({val: `/aux/${i}/mute`, label: `Aux In ${i}`});
                    for(let i=1; i<=16; i++) options.push({val: `/bus/${i}/mute`, label: `Bus ${i}`});
                    for(let i=1; i<=4; i++) options.push({val: `/main/${i}/mute`, label: `Main ${i}`});
                    for(let i=1; i<=8; i++) options.push({val: `/mtx/${i}/mute`, label: `Matrix ${i}`});
                }
                
                const optsHtml = options.map(o => `<option value="${o.val}" ${current === o.val ? 'selected' : ''}>${o.label}</option>`).join('');
                return `<div style="margin-top: 10px;">
                    <label>Monitor Target</label>
                    <select onchange="updateState(${led.id}, 'target', this.value)">
                        <option value="">-- Select Target --</option>
                        ${optsHtml}
                    </select>
                </div>`;
            }
            
            return `<div style="margin-top: 10px;">
                <label>Target Identifier</label>
                <input type="text" value="${escHtml(current)}" oninput="updateState(${led.id}, 'target', this.value)" placeholder="ID or Path">
            </div>`;
        }

        function render() {
            const container = document.getElementById('app');
            container.innerHTML = '';
            
            const currentHost = window.location.host;
            
            // Global Settings
            const globalSettings = document.createElement('div');
            globalSettings.className = 'led-card';
            
            // Mixers only in global
            const connTypes = ['x32', 'wing'];
            const connectionsHtml = connTypes.map(type => `
                <div style="display: flex; gap: 10px; margin-bottom: 10px; align-items: center;">
                    <label style="width: 80px; text-transform: capitalize;">${type}</label>
                    <input type="text" value="${currentState.connections[type]?.ip || ''}" 
                        oninput="updateConnection('${type}', 'ip', this.value)" placeholder="Mixer IP" style="flex: 2; padding: 8px;">
                    <input type="number" value="${currentState.connections[type]?.port || 0}" 
                        oninput="updateConnection('${type}', 'port', parseInt(this.value))" placeholder="Port" style="flex: 1; padding: 8px; width: 60px;">
                </div>
            `).join('');

            globalSettings.innerHTML = `
                <div class="led-header">
                    <span style="font-weight: bold; font-size: 1.1em;">Global Mixer Connections</span>
                </div>
                
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin-top: 10px;">
                    ${connectionsHtml}
                </div>

                <div style="margin-top: 20px; border-top: 1px solid #333; padding-top: 20px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                        <label>Show Local Preview Window</label>
                        <label class="switch">
                            <input type="checkbox" ${currentState.show_preview ? 'checked' : ''} onchange="currentState.show_preview = this.checked">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                        <label>Show LED Indicators</label>
                        <label class="switch">
                            <input type="checkbox" ${currentState.show_leds !== false ? 'checked' : ''} onchange="currentState.show_leds = this.checked">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                        <label>Show Channel Names</label>
                        <label class="switch">
                            <input type="checkbox" ${currentState.show_names !== false ? 'checked' : ''} onchange="currentState.show_names = this.checked">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                        <label>Show Battery Level</label>
                        <label class="switch">
                            <input type="checkbox" ${currentState.show_battery !== false ? 'checked' : ''} onchange="currentState.show_battery = this.checked">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div>
                        <label>Layout Mode</label>
                        <select onchange="currentState.layout_mode = this.value">
                            <option value="fixed" ${currentState.layout_mode !== 'spaced' ? 'selected' : ''}>Fixed Slots (Leave Gaps)</option>
                            <option value="spaced" ${currentState.layout_mode === 'spaced' ? 'selected' : ''}>Space Active Channels Evenly</option>
                        </select>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 15px; border-top: 1px solid #333; padding-top: 15px;">
                        <label style="color: var(--danger);">Enable Debug Logging</label>
                        <div style="display: flex; gap: 15px; align-items: center;">
                            <a href="/api/logs/download" target="_blank" style="color: var(--accent); font-size: 0.9em; text-decoration: none;">Download Log</a>
                            <label class="switch">
                                <input type="checkbox" ${currentState.enable_debug_logging ? 'checked' : ''} onchange="currentState.enable_debug_logging = this.checked">
                                <span class="slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(globalSettings);

            currentState.leds.forEach(led => {
                const card = document.createElement('div');
                card.className = 'led-card';
                
                card.innerHTML = `
                    <div class="led-header">
                        <span class="led-id">Channel ${led.id + 1}</span>
                        <label class="switch">
                            <input type="checkbox" ${led.enabled ? 'checked' : ''} onchange="updateState(${led.id}, 'enabled', this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                         <div style="flex: 2;">
                            <label>Display Name</label>
                            <input type="text" value="${escHtml(led.name)}" oninput="updateState(${led.id}, 'name', this.value)">
                         </div>
                         ${['shure', 'sennheiser'].includes(led.monitor_type) ? `
                         <div style="flex: 1; min-width: 80px;">
                            <label>Sync Name</label>
                            <label class="switch" style="transform: scale(0.8); margin-top: 5px;">
                                <input type="checkbox" ${led.use_receiver_name ? 'checked' : ''} onchange="updateState(${led.id}, 'use_receiver_name', this.checked)">
                                <span class="slider"></span>
                            </label>
                        </div>
                         ` : ''}
                    </div>

                    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin-top: 10px;">
                        <label style="color: var(--accent); font-weight: bold; font-size: 0.8em; text-transform: uppercase; display: block; margin-bottom: 10px;">Monitor Configuration</label>
                        
                        <div style="margin-bottom: 10px;">
                            <label>Monitor Type</label>
                            <select onchange="updateState(${led.id}, 'monitor_type', this.value); render();">
                                <option value="shure" ${led.monitor_type === 'shure' ? 'selected' : ''}>Shure</option>
                                <option value="sennheiser" ${led.monitor_type === 'sennheiser' ? 'selected' : ''}>Sennheiser</option>
                                <option value="x32" ${led.monitor_type === 'x32' ? 'selected' : ''}>X32 / M32</option>
                                <option value="wing" ${led.monitor_type === 'wing' ? 'selected' : ''}>WING</option>
                                <option value="api" ${led.monitor_type === 'api' ? 'selected' : ''}>API Endpoint</option>
                            </select>
                        </div>

                        ${getTargetSelector(led)}
                    </div>

                    <div style="margin-top: 10px; display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <label>Flash Interval (ms)</label>
                            <input type="number" value="${led.interval}" oninput="updateState(${led.id}, 'interval', parseInt(this.value))" style="width: 100px;">
                        </div>
                        ${led.monitor_type !== 'api' ? `
                        <div style="text-align: right;">
                             <label>Use Live Status</label>
                             <label class="switch" style="margin-top: 5px;">
                                <input type="checkbox" ${led.use_live_status ? 'checked' : ''} onchange="updateState(${led.id}, 'use_live_status', this.checked)">
                                <span class="slider"></span>
                            </label>
                        </div>
                        ` : ''}
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function updateState(id, key, value) {
            const led = currentState.leds.find(l => l.id === id);
            if (led) { led[key] = value; }
        }

        async function saveConfig() {
            const btn = document.querySelector('.btn-save');
            const originalText = btn.innerText;
            btn.innerText = "Saving...";
            
            try {
                await fetch('/api/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 
                        leds: currentState.leds,
                        connections: currentState.connections,
                        show_preview: currentState.show_preview,
                        show_leds: currentState.show_leds,
                        show_names: currentState.show_names,
                        show_battery: currentState.show_battery,
                        layout_mode: currentState.layout_mode,
                        enable_debug_logging: currentState.enable_debug_logging
                    })
                });
                btn.innerText = "Saved!";
                setTimeout(() => btn.innerText = originalText, 2000);
            } catch (e) {
                btn.innerText = "Error!";
                console.error(e);
            }
        }

        fetchConfig();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    return dashboard_html

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

if __name__ == "__main__":
    run_server()

