from flask import Flask, render_template, jsonify, request
import requests
import time

app = Flask(__name__)

# ---- CONFIGURATION ----
# The IP address of your Raspberry Pi 2 (Gateway)
# Ensure this matches the IP printed in your RPi 2 terminal
RPI2_IP = "192.168.137.230"
RPI2_PORT = 5050

# ---------------- HOME PAGE ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- GET LIVE DATA ----------------
# The website calls this function every 2 seconds to get updates.
@app.route("/api/data")
def api_data():
    try:
        # 1. Request data from Raspberry Pi 2
        r = requests.get(f"http://{RPI2_IP}:{RPI2_PORT}/api/data", timeout=2)
        
        if r.status_code == 200:
            rpi_data = r.json()
            
            # 2. Forward the COMPLETE packet to the website
            # We do NOT filter fields here. We send everything (sensors, alerts, crop, etc.)
            # This ensures the website sees the "alerts" and "fertilizer_prediction" keys.
            return jsonify(rpi_data)
        
        else:
            print(f"⚠️ RPi2 returned status code: {r.status_code}")
            return jsonify({"error": "RPi2 Error", "status": "CONNECTION ERROR"})

    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        # Return a 'Disconnected' state so the UI doesn't freeze
        return jsonify({
            "error": "RPi2 Offline",
            "status": "DISCONNECTED",
            "sensors": {}, 
            "alerts": {},
            "last_update": "Offline"
        })

# ---------------- SEND CROP COMMAND ----------------
# The website calls this when you click "Set Crop"
@app.route("/api/set-crop", methods=["POST"])
def set_crop():
    data = request.get_json()
    crop = data.get("crop")

    if not crop:
        return jsonify({"error": "No crop selected"}), 400

    try:
        # Forward the command to Raspberry Pi 2
        response = requests.post(
            f"http://{RPI2_IP}:{RPI2_PORT}/api/set-crop",
            json={"crop": crop},
            timeout=2
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully set crop to: {crop}")
            return jsonify({"status": "ok", "message": f"Set crop to {crop}"})
        else:
            return jsonify({"error": "RPi2 failed to set crop"}), 500

    except Exception as e:
        print(f"❌ Failed to send crop command: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print(f"✅ Website running at http://127.0.0.1:8000")
    print(f"🔗 Connecting to RPi 2 at http://{RPI2_IP}:{RPI2_PORT}")
    
    # Run the server
    app.run(host="0.0.0.0", port=8000, debug=True)