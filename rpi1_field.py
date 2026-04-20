import serial
import time
import board
import adafruit_dht
import spidev
import RPi.GPIO as GPIO
import json
import minimalmodbus


# ============================================================
# ---------------- Load Crop Database -------------------------
# ============================================================

with open('crop_profiles.json', 'r') as f:
    CROP_DB = json.load(f)
    print("âœ“ Crop database loaded successfully")


# ============================================================
# ------------------- Global Settings -------------------------
# ============================================================

PORT_NAME = '/dev/serial/by-id/usb-FTDI_USB_Serial_Converter_FTB6SPL3-if00-port0'
SLAVE_ADDRESS = 1
BAUD_RATE = 9600

PORT = "/dev/ttyS0"
BAUD = 9600

CS_PIN = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(CS_PIN, GPIO.OUT)
GPIO.output(CS_PIN, GPIO.HIGH)

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

dhtDevice = adafruit_dht.DHT11(board.D21)

REG_N_ALT = 30
REG_P_ALT = 31
REG_K_ALT = 32


# ============================================================
# ---------------- Helper Functions ---------------------------
# ============================================================

def read_channel(channel):
    GPIO.output(CS_PIN, GPIO.LOW)
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    GPIO.output(CS_PIN, GPIO.HIGH)
    return ((adc[1] & 3) << 8) | adc[2]


def convert_volts(data, vref=3.3):
    return round((data * vref) / 1023.0, 2)


def check_status(value, limits):
    low, high = limits
    if value is None:
        return "NO DATA"
    if value < low:
        return "LOW"
    if value > high:
        return "HIGH"
    return "OK"


# ============================================================
# ---------------- Initialize LoRa & Modbus -------------------
# ============================================================

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print(f"âœ“ LoRa started on {PORT}")
except:
    print("âœ— LoRa failed!")
    ser = None

try:
    instrument = minimalmodbus.Instrument(PORT_NAME, SLAVE_ADDRESS)
    instrument.serial.baudrate = BAUD_RATE
    instrument.serial.parity = serial.PARITY_EVEN
    instrument.mode = minimalmodbus.MODE_RTU
    print("âœ“ Modbus connected")
except:
    print("âœ— Modbus failed")
    instrument = None


# ============================================================
# ---------------- Sensor Reading Functions -------------------
# ============================================================

def read_npk():
    if instrument is None:
        return None, None, None
    try:
        n = instrument.read_register(REG_N_ALT, 0, 3)
        p = instrument.read_register(REG_P_ALT, 0, 3)
        k = instrument.read_register(REG_K_ALT, 0, 3)
        return n, p, k
    except:
        return None, None, None


def read_dht():
    try:
        return dhtDevice.temperature, dhtDevice.humidity
    except:
        return None, None


def read_voltage():
    return convert_volts(read_channel(0))


# ============================================================
# ------------------ LoRa RX Logic ----------------------------
# ============================================================

def receive_lora_data():
    if ser is None or not ser.is_open:
        return None

    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode().strip()
            incoming = json.loads(line)
            crop = incoming.get("crop", "").lower()

            if crop in CROP_DB:
                ideal = CROP_DB[crop]

                return {
                    "crop": crop,
                    "ideals": {
                        "N": ideal["N"],
                        "P": ideal["P"],
                        "K": ideal["K"],
                        "Temp": ideal["temperature"],
                        "Hum": ideal["humidity"]
                    },
                    "ranges": {
                        "N": [ideal["N"] - 10, ideal["N"] + 10],
                        "P": [ideal["P"] - 10, ideal["P"] + 10],
                        "K": [ideal["K"] - 10, ideal["K"] + 10],
                        "Temp": [ideal["temperature"] - 5, ideal["temperature"] + 5],
                        "Hum": [ideal["humidity"] - 10, ideal["humidity"] + 10]
                    }
                }
        except:
            return None

    return None


# ============================================================
# --------------------------- MAIN ----------------------------
# ============================================================

if __name__ == "__main__":
    active_profile = None
    packet_counter = 0

    try:
        while True:

            # 1. Check if user selected crop
            new_profile = receive_lora_data()
            if new_profile:
                active_profile = new_profile
                print(f"âœ“ Crop selected: {active_profile['crop']}")

            # If no crop selected â†’ skip sending
            if active_profile is None:
                time.sleep(2)
                continue

            # 2. Read sensors
            temp, hum = read_dht()
            voltage = read_voltage()
            n, p, k = read_npk()

            # Base packet
            packet = {
                "id": packet_counter,
                "sensors": {
                    "Temp": temp,
                    "Hum": hum,
                    "Volt": voltage,
                    "N": n,
                    "P": p,
                    "K": k
                },
                "alerts": {}
            }

            # ALERT LOGIC
            ranges = active_profile["ranges"]
            ideals = active_profile["ideals"]

            status_temp = check_status(temp, ranges["Temp"])
            status_hum = check_status(hum, ranges["Hum"])
            status_n = check_status(n, ranges["N"])
            status_p = check_status(p, ranges["P"])
            status_k = check_status(k, ranges["K"])

            npk_outside = (status_n != "OK" or status_p != "OK" or status_k != "OK")
            temp_hum_outside = (status_temp != "OK" or status_hum != "OK")

            # --------------------------------------------
            # CASE 1 â†’ ANY NPK OUTSIDE â†’ SEND FULL SENSOR DATA + ALL ALERTS
            # --------------------------------------------
            if npk_outside:
                if status_n != "OK":
                    packet["alerts"]["N"] = f"N is {status_n}! Value:{n}, Ideal:{ideals['N']}"
                if status_p != "OK":
                    packet["alerts"]["P"] = f"P is {status_p}! Value:{p}, Ideal:{ideals['P']}"
                if status_k != "OK":
                    packet["alerts"]["K"] = f"K is {status_k}! Value:{k}, Ideal:{ideals['K']}"
                if status_temp != "OK":
                    packet["alerts"]["Temp"] = f"Temperature is {status_temp}! Value:{temp}, Ideal:{ideals['Temp']}"
                if status_hum != "OK":
                    packet["alerts"]["Hum"] = f"Humidity is {status_hum}! Value:{hum}, Ideal:{ideals['Hum']}"

            # --------------------------------------------
            # CASE 2 â†’ ONLY TEMP/HUM OUTSIDE â†’ SEND ONLY TEMP/HUM ALERTS
            # --------------------------------------------
            elif temp_hum_outside:
                if status_temp != "OK":
                    packet["alerts"]["Temp"] = f"Temperature is {status_temp}! Value:{temp}, Ideal:{ideals['Temp']}"
                if status_hum != "OK":
                    packet["alerts"]["Hum"] = f"Humidity is {status_hum}! Value:{hum}, Ideal:{ideals['Hum']}"
                # Remove NPK because they are fine
                packet["sensors"].pop("N")
                packet["sensors"].pop("P")
                packet["sensors"].pop("K")

            # --------------------------------------------
            # CASE 3 â†’ ALL OK â†’ send normal sensor data, no alerts
            # --------------------------------------------
            else:
                packet["alerts"] = {}

            # SEND PACKET
            ser.write(json.dumps(packet).encode())
            print("Sent â†’", packet)

            packet_counter += 1
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nâœ“ Stopped")

    finally:
        GPIO.cleanup()
