from flask import Flask, request, jsonify, render_template
import serial
import threading
import json
import time
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)

# ---------------- CONFIG ----------------
SERIAL_PORTS = ["/dev/serial0", "/dev/ttyAMA0", "/dev/ttyS0"]
BAUD_RATE = 9600

ser = None

for port in SERIAL_PORTS:
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        print(f"âœ“ LoRa Connected on {port}")
        break
    except:
        pass

if ser is None:
    print("âš  LoRa NOT connected (but website still runs)")


# ---------------- LOAD ML MODELS ----------------
print("ðŸ“¦ Loading ML models...")

scaler = joblib.load("data_scaler.joblib")
fertilizer_model = joblib.load("fertilizer_model.joblib")
label_encoder = joblib.load("label_encoder.joblib")

print("âœ… ML models loaded successfully!")


# ---------------- GLOBAL STATE ----------------
dashboard_data = {
    "sensors": {
        "Temp": "--",
        "Hum": "--",
        "Volt": "--",
        "N": "--",
        "P": "--",
        "K": "--"
    },
    "alerts": {},
    "fertilizer_recommendation": "None",   # <<< NEW FIELD HERE
    "crop_target": "None",
    "last_update": "Waiting..."
}


# ---------------- ML PREDICTION FUNCTION ----------------
def predict_fertilizer(temp, hum, volt, N, P, K):
    df_input = pd.DataFrame([{
        "Temparature": temp,
        "Humidity ": hum,
        "Moisture": volt,
        "Nitrogen": N,
   
        "Potassium": K,
        "Phosphorous": P
    }])

    scaled = scaler.transform(df_input)
    pred = fertilizer_model.predict(scaled)[0]
    fertilizer = label_encoder.inverse_transform([pred])[0]

    return fertilizer


# ---------------- WEBSITE ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    return jsonify(dashboard_data)

@app.route('/api/set-crop', methods=['POST'])
def set_crop():
    data = request.json or {}
    crop_name = data.get('crop', "unknown")

    dashboard_data["crop_target"] = crop_name
    dashboard_data["last_update"] = time.strftime("%H:%M:%S")

    print(f"ðŸŒ± Crop Selected: {crop_name}")

    if ser and ser.is_open:
        try:
            msg = json.dumps({"crop": crop_name}) + "\n"
            ser.write(msg.encode())
            print("ðŸ“¡ Sent crop to RPi1 via LoRa")
        except Exception as e:
            print("âš  LoRa TX Error:", e)

    return jsonify({"status": "ok"})


# ---------------- LORA RECEIVER THREAD ----------------
def listen_lora():
    global dashboard_data
    print("ðŸ“¡ Listening for LoRa messages...")

    while True:
        if ser and ser.in_waiting > 0:
            try:
                raw = ser.readline().decode(errors="ignore").strip()

                if not raw or not raw.startswith("{"):
                    continue

                print(f"\nðŸ“¥ Received: {raw}")

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    print("âš  Ignored corrupt LoRa packet")
                    continue

                # Update dashboard sensors
                if "sensors" in data:
                    dashboard_data["sensors"] = data["sensors"]

                alerts = data.get("alerts", {})
                dashboard_data["alerts"] = alerts
                dashboard_data["last_update"] = time.strftime("%H:%M:%S")

                # Extract sensor values
                temp = data["sensors"]["Temp"]
                hum = data["sensors"]["Hum"]
                volt = data["sensors"]["Volt"]
                N = data["sensors"]["N"]
                P = data["sensors"]["P"]
                K = data["sensors"]["K"]

                npk_alerts = any(k in alerts for k in ["N", "P", "K"])

                if npk_alerts:
                    print("âš  NPK ALERTS DETECTED:")
                    for nutrient in ["N", "P", "K"]:
                        if nutrient in alerts:
                            print(" â€¢", alerts[nutrient])

                    # Predict fertilizer
                    fertilizer = predict_fertilizer(temp, hum, volt, N, P, K)
                    print(f"ðŸ’¡ Recommended Fertilizer: {fertilizer}")

                    # <<< STORE IN DASHBOARD SO WEB CAN SHOW IT
                    dashboard_data["fertilizer_recommendation"] = fertilizer

                else:
                    print("ðŸŒ¤ Environmental Status Only:")
                    print(f" â€¢ Temp: {temp}Â°C (Ideal: 25â€“30Â°C)")
                    print(f" â€¢ Humidity: {hum}% (Ideal: 60â€“80%)")

                    # No fertilizer needed
                    dashboard_data["fertilizer_recommendation"] = "None"

            except Exception as e:
                print("âš  LoRa RX Error:", e)

        time.sleep(0.1)


# ---------------- MAIN ----------------
if __name__ == '__main__':
    t = threading.Thread(target=listen_lora)
    t.daemon = True
    t.start()

    app.run(host='0.0.0.0', port=5050, debug=True, use_reloader=False)
