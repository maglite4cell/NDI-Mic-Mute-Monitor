from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import threading
from state import state
import os

app = FastAPI()

# Input Models
class LedUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    enabled: Optional[bool] = None
    interval: Optional[int] = None
    shure_ip: Optional[str] = None
    shure_port: Optional[int] = None
    use_receiver_name: Optional[bool] = None
    use_live_status: Optional[bool] = None

class ConfigUpdate(BaseModel):
    leds: List[LedUpdate]
    show_preview: Optional[bool] = None
    show_leds: Optional[bool] = None
    show_names: Optional[bool] = None
    layout_mode: Optional[str] = None

# API Endpoints
@app.get("/api/config")
def get_config():
    return state.config

@app.post("/api/config")
def update_config(update: ConfigUpdate):
    for item in update.leds:
        state.update_led(item.id, item.dict(exclude_unset=True))
    
    if update.show_preview is not None:
        state.config["show_preview"] = update.show_preview
    if update.show_leds is not None:
        state.config["show_leds"] = update.show_leds
    if update.show_names is not None:
        state.config["show_names"] = update.show_names
    if update.layout_mode is not None:
        state.config["layout_mode"] = update.layout_mode
        
    state.save_config()
        
    return {"status": "ok", "config": state.config}



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
            max_width: 800px;
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
        
        input[type="text"] {
            background: #2c2c2c;
            border: 1px solid #333;
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-size: 16px; /* Preventing iOS zoom */
            width: 100%;
            box-sizing: border-box;
        }

        input[type="number"] {
            background: #2c2c2c;
            border: 1px solid #333;
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-size: 16px;
            width: 100px;
        }

        .controls {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-top: 10px;
        }

        label { font-size: 0.9em; opacity: 0.8; }

        /* Custom Toggle Switch */
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
        let currentState = { leds: [] };

        async function fetchConfig() {
            // Fetch LED Config
            const res = await fetch('/api/config');
            const data = await res.json();
            currentState = data;
            render();
        }


        function render() {
            const container = document.getElementById('app');
            container.innerHTML = '';
            
            // Global Settings
            const globalSettings = document.createElement('div');
            globalSettings.className = 'led-card';
            globalSettings.innerHTML = `
                <div class="led-header">
                    <span style="font-weight: bold; font-size: 1.1em;">Global Settings</span>
                </div>
                <div style="margin-top: 15px; display: flex; align-items: center; justify-content: space-between;">
                    <label>Show Local Preview Window</label>
                    <label class="switch">
                        <input type="checkbox" ${currentState.show_preview ? 'checked' : ''} 
                            onchange="currentState.show_preview = this.checked">
                        <span class="slider"></span>
                    </label>
                </div>
                <div style="margin-top: 15px; display: flex; align-items: center; justify-content: space-between;">
                    <label>Show LED Indicators</label>
                    <label class="switch">
                        <input type="checkbox" ${currentState.show_leds !== false ? 'checked' : ''} 
                            onchange="currentState.show_leds = this.checked">
                        <span class="slider"></span>
                    </label>
                </div>
                <div style="margin-top: 15px; display: flex; align-items: center; justify-content: space-between;">
                    <label>Show Channel Names</label>
                    <label class="switch">
                        <input type="checkbox" ${currentState.show_names !== false ? 'checked' : ''} 
                            onchange="currentState.show_names = this.checked">
                        <span class="slider"></span>
                    </label>
                </div>
                <div style="margin-top: 15px;">
                    <label style="display: block; margin-bottom: 5px;">Layout Mode</label>
                    <select onchange="currentState.layout_mode = this.value" style="width: 100%; padding: 10px; background: #2c2c2c; color: white; border: 1px solid #333; border-radius: 8px;">
                        <option value="fixed" ${currentState.layout_mode !== 'spaced' ? 'selected' : ''}>Fixed Slots (Leave Gaps)</option>
                        <option value="spaced" ${currentState.layout_mode === 'spaced' ? 'selected' : ''}>Space Active Channels Evenly</option>
                    </select>
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
                            <input type="checkbox" ${led.enabled ? 'checked' : ''} 
                                onchange="updateState(${led.id}, 'enabled', this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                         <div style="flex: 2;">
                            <label>Display Name</label>
                            <input type="text" value="${led.name}" 
                                oninput="updateState(${led.id}, 'name', this.value)">
                         </div>
                         <div style="flex: 1; min-width: 80px;">
                            <label>Sync Name</label>
                            <label class="switch" style="transform: scale(0.8); margin-top: 5px;">
                                <input type="checkbox" ${led.use_receiver_name ? 'checked' : ''} 
                                    onchange="updateState(${led.id}, 'use_receiver_name', this.checked)">
                                <span class="slider"></span>
                            </label>
                        </div>
                    </div>

                    <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-top: 10px;">
                        <label style="color: var(--accent); font-weight: bold; font-size: 0.8em; text-transform: uppercase; display: block; margin-bottom: 5px;">Receiver Connection</label>
                        <div class="controls">
                            <div style="flex: 3;">
                                <label>IP Address</label>
                                <input type="text" value="${led.shure_ip || '127.0.0.1'}" 
                                    oninput="updateState(${led.id}, 'shure_ip', this.value)">
                            </div>
                            <div style="flex: 1;">
                                <label>Port</label>
                                <input type="number" value="${led.shure_port || 2202}" 
                                    oninput="updateState(${led.id}, 'shure_port', parseInt(this.value))">
                            </div>
                        </div>
                    </div>

                    <div style="margin-top: 10px; display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <label style="display: block;">Flash Interval (ms)</label>
                            <input type="number" value="${led.interval}" 
                                oninput="updateState(${led.id}, 'interval', parseInt(this.value))"
                                style="width: 100px;">
                        </div>
                        <div style="text-align: right;">
                             <label style="display: block;">Use Live Status</label>
                             <label class="switch" style="margin-top: 5px;">
                                <input type="checkbox" ${led.use_live_status ? 'checked' : ''} 
                                    onchange="updateState(${led.id}, 'use_live_status', this.checked)">
                                <span class="slider"></span>
                            </label>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function updateState(id, key, value) {
            const led = currentState.leds.find(l => l.id === id);
            if (led) {
                led[key] = value;
            }
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
                        show_preview: currentState.show_preview,
                        show_leds: currentState.show_leds,
                        show_names: currentState.show_names,
                        layout_mode: currentState.layout_mode
                    })
                });
                btn.innerText = "Saved!";
                setTimeout(() => btn.innerText = originalText, 2000);
            } catch (e) {
                btn.innerText = "Error!";
                console.error(e);
            }
        }

        // Initial Load
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
