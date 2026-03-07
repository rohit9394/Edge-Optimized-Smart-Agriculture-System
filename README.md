# 🌱 Smart Farm Monitoring & AI Fertilizer Recommendation System

This project is an **IoT-based smart farming system** designed to monitor environmental and soil conditions in real time and provide **AI-based fertilizer recommendations** to farmers.

The system uses **two Raspberry Pi devices communicating through LoRa**, a **Flask web server**, and **machine learning models** to assist farmers in maintaining optimal crop conditions.

The dashboard displays real-time data such as:

- Temperature
- Humidity
- Soil moisture
- Nitrogen (N)
- Phosphorus (P)
- Potassium (K)
- Environmental alerts
- AI fertilizer recommendation

The main goal of this project is to help farmers **make data-driven decisions for crop health and fertilizer usage**.

---

# 📡 System Architecture

```
Field Sensors
 (Temp, Humidity, Soil Moisture, NPK)
          │
          ▼
 Raspberry Pi 1 (Field Node)
  - Reads sensors
  - Applies crop profile rules
  - Sends data via LoRa
          │
          ▼
 Raspberry Pi 2 (Gateway Node)
  - Receives LoRa packets
  - Runs Machine Learning model
  - Hosts Flask API
          │
          ▼
 Web Server (Flask Dashboard)
          │
          ▼
 Live Smart Farm Dashboard
```

---

# 🧰 Hardware Components

## Field Node (Raspberry Pi 1)

- Raspberry Pi
- DHT11 Temperature and Humidity Sensor
- Soil Moisture Sensor (via SPI ADC)
- NPK Soil Sensor (Modbus)
- LoRa Module
- MCP3008 ADC
- Power supply and connecting wires

## Gateway Node (Raspberry Pi 2)

- Raspberry Pi
- LoRa Module
- Flask Web Server
- Machine Learning models

---

# 💻 Software Technologies

- Python
- Flask (Web Framework)
- Machine Learning (Scikit-learn)
- TensorFlow Lite
- LoRa Serial Communication
- HTML / CSS / JavaScript
- JSON Data Processing

---

# ⚙️ Key Features

## Real-Time Farm Monitoring

The system continuously monitors:

- Temperature
- Humidity
- Soil moisture
- Nitrogen
- Phosphorus
- Potassium

All sensor values are displayed on the **web dashboard in real time**.

---

## Intelligent Crop Profiles

Each crop has predefined **ideal environmental conditions** stored in:

```
crop_profiles.json
```

Example parameters include:

- Ideal NPK values
- Temperature
- Humidity
- Rainfall
- Soil pH

These profiles allow the system to compare current field conditions with **ideal crop conditions**.

---

## Automatic Alert System

The system generates alerts when conditions move outside the ideal range.

Examples:

- Nitrogen Low
- Phosphorus High
- Potassium Low
- Temperature High
- Humidity Low

Alerts are displayed on the dashboard to notify the user.

---

## 🤖 AI Fertilizer Recommendation

When nutrient imbalance is detected, the system uses a **machine learning model** to recommend the best fertilizer.

### Machine Learning Model

Algorithm used:

```
RandomForestClassifier
```

Input features:

- Temperature
- Humidity
- Soil moisture
- Nitrogen
- Phosphorus
- Potassium

Output:

```
Recommended fertilizer
```

Libraries used:

- scikit-learn
- pandas
- numpy
- joblib

---

# 📡 LoRa Communication

The system uses **LoRa modules** to communicate between two Raspberry Pi devices.

### Raspberry Pi 1 (Field Node)

- Reads sensor values
- Creates a JSON packet
- Sends the packet through LoRa

Example packet:

```json
{
  "sensors": {
    "Temp": 28,
    "Hum": 70,
    "Volt": 2.3,
    "N": 30,
    "P": 40,
    "K": 20
  },
  "alerts": {
    "N": "Nitrogen is LOW"
  }
}
```

---

### Raspberry Pi 2 (Gateway)

- Receives LoRa packets
- Processes alerts
- Runs fertilizer prediction
- Sends data to the dashboard

---

# 🌐 Web Dashboard

The web dashboard is built using:

- Flask
- HTML
- CSS
- JavaScript

Features of the dashboard:

- Live sensor updates every **2 seconds**
- Crop selection interface
- Real-time alerts
- AI fertilizer recommendation
- System status indicator

System status types:

| Status | Meaning |
|------|------|
SYSTEM OPTIMAL | All conditions normal |
WARNING | Environmental issue detected |
CRITICAL | Nutrient imbalance detected |

---

# 🔗 API Endpoints

### Get Live Data

```
GET /api/data
```

Returns the latest sensor data and alerts.

---

### Set Crop Profile

```
POST /api/set-crop
```

Example request:

```json
{
  "crop": "rice"
}
```

This sends the selected crop to the **field node through LoRa**.

---

# 📂 Project Structure

```
smart-farm-system
│
├── rpi1_field.py
├── rpi2.py
├── app.py
│
├── models
│   ├── fertilizer_model.joblib
│   ├── data_scaler.joblib
│   └── label_encoder.joblib
│
├── ml_training
│   ├── crop_prediction_model.py
│   └── convert_model.py
│
├── crop_profiles.json
│
├── templates
│   └── index.html
│
└── README.md
```

---

# ⚡ Installation

Install required Python libraries:

```
pip install flask numpy pandas scikit-learn joblib pyserial requests
```

For Raspberry Pi sensors:

```
pip install adafruit-circuitpython-dht
pip install spidev
pip install minimalmodbus
```

---

# 🚀 Running the System

### Step 1 — Start Field Node

```
python rpi1_field.py
```

Reads sensors and sends LoRa packets.

---

### Step 2 — Start Gateway Node

```
python rpi2.py
```

Receives LoRa packets and runs the ML model.

---

### Step 3 — Run the Web Server

```
python app.py
```

Open dashboard:

```
http://localhost:8000
```

---

# 🔄 Example Workflow

1. User selects crop on the dashboard.
2. Crop profile is sent to Raspberry Pi 1 via LoRa.
3. Sensors read field conditions.
4. Data is transmitted to Raspberry Pi 2.
5. Gateway evaluates conditions.
6. ML model predicts fertilizer if nutrients are outside range.
7. Dashboard displays alerts and recommendations.

---

# 🔮 Future Improvements

- Cloud database for storing historical data
- Mobile application for farmers
- AI irrigation automation
- Crop yield prediction
- Remote monitoring through IoT cloud platforms

---

# 👨‍💻 Author

**Rohit Sharma**

Digital System Lab Project  
IoT + Machine Learning based Smart Agriculture System

---
