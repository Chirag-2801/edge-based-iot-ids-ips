import paho.mqtt.client as mqtt
import json
import csv
import datetime
import joblib
import requests
import os
import math  

# -------------------------
# CONFIG
# -------------------------
BROKER = os.getenv("BROKER_IP")
PORT = int(os.getenv("BROKER_PORT"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

model = joblib.load("model.pkl")
scaler = joblib.load("scaler.pkl")

packet_count = 0
start_time = datetime.datetime.now()

blocked_ips = set()
blocked_time = {}

COOLDOWN = 20   # seconds

# -------------------------
# STATISTICAL MODEL CONFIG (NEW)
# -------------------------
rate_history = []
WINDOW_SIZE = 20


# -------------------------
# TELEGRAM
# -------------------------
def send_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except:
        print("Telegram error")


# -------------------------
# BLOCK IP
# -------------------------
def block_ip(ip):

    if ip in blocked_ips or ip == "unknown":
        return

    print(f"🚫 Blocking IP: {ip}")

    os.system(f'netsh advfirewall firewall add rule name="Block_IN_{ip}" dir=in action=block remoteip={ip}')
    os.system(f'netsh advfirewall firewall add rule name="Block_OUT_{ip}" dir=out action=block remoteip={ip}')

    blocked_ips.add(ip)
    blocked_time[ip] = datetime.datetime.now()

    print(f"✅ IP {ip} BLOCKED")


# -------------------------
# LOG ONLY ATTACKS
# -------------------------
def log_data(rate, status, ip):
    with open("traffic_log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now(),
            rate,
            status,
            ip
        ])


# -------------------------
# ML DETECTION
# -------------------------
def ml_detect(temp, pressure):
    X = [[temp, pressure]]
    X_scaled = scaler.transform(X)
    result = model.predict(X_scaled)
    return result[0] == -1


# -------------------------
# CALLBACK
# -------------------------
def on_message(client, userdata, msg):

    global packet_count, start_time

    packet_count += 1

    try:
        data = json.loads(msg.payload.decode())

        device = data.get("device", "unknown")
        ip = data.get("ip", "unknown")

        # -------------------------
        # IGNORE BLOCKED (COOLDOWN)
        # -------------------------
        if ip in blocked_time:
            elapsed_block = (datetime.datetime.now() - blocked_time[ip]).total_seconds()
            if elapsed_block < COOLDOWN:
                return

        # -------------------------
        # SENSOR LOGGING
        # -------------------------
        if device == "dht11":

            temp = data.get("temperature")
            pressure = data.get("pressure")

            ml_attack = ml_detect(temp, pressure)

            with open("sensor_data.csv", "a", newline="") as f:
                csv.writer(f).writerow([
                    datetime.datetime.now(),
                    temp,
                    pressure,
                    ""
                ])

        elif device == "ldr":

            ml_attack = False

            with open("sensor_data.csv", "a", newline="") as f:
                csv.writer(f).writerow([
                    datetime.datetime.now(),
                    "",
                    "",
                    data.get("light")
                ])

        else:
            ml_attack = False

        # -------------------------
        # RATE CHECK
        # -------------------------
        elapsed = (datetime.datetime.now() - start_time).total_seconds()

        if elapsed >= 5:

            rate = packet_count / elapsed

            # -------------------------
            # STATISTICAL DETECTION (Z-SCORE)
            # -------------------------
            global rate_history

            rate_history.append(rate)

            if len(rate_history) > WINDOW_SIZE:
                rate_history.pop(0)

            if len(rate_history) >= 5:
                mean_rate = sum(rate_history) / len(rate_history)

                variance = sum((x - mean_rate) ** 2 for x in rate_history) / len(rate_history)
                std_dev = math.sqrt(variance)

                if std_dev != 0:
                    z_score = (rate - mean_rate) / std_dev
                    flood_attack = z_score > 3
                else:
                    flood_attack = False
            else:
                flood_attack = False

            # -------------------------
            # ATTACK DECISION
            # -------------------------
            if flood_attack or ml_attack:

                attack_type = "FLOOD" if flood_attack else "ML ANOMALY"

                print(f"🚨 ATTACK DETECTED | {attack_type} | IP: {ip}")

                log_data(rate, "ATTACK", ip)

                send_alert(f"🚨 {attack_type}\nIP: {ip}\nRate: {round(rate,2)}")

                block_ip(ip)

            else:
                print(f"✅ NORMAL | Rate: {round(rate,2)}")
                log_data(rate, "NORMAL", ip)

            packet_count = 0
            start_time = datetime.datetime.now()

    except Exception as e:
        print("Error:", e)


# -------------------------
# MAIN
# -------------------------
print("🚀 FINAL IPS STARTED...")

client = mqtt.Client()
client.connect(BROKER, PORT)

client.subscribe("iot/#")
client.on_message = on_message

client.loop_forever()