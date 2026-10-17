import paho.mqtt.client as mqtt
import json
import csv

BROKER = os.getenv("BROKER_IP")
PORT = int(os.getenv("BROKER_PORT"))

print("📡 Collecting NORMAL data for ML...")

# create file
with open("normal_traffic.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["temperature", "pressure"])  # features


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        if data.get("device") == "dht11":

            temp = data.get("temperature")
            pressure = data.get("pressure")

            # only valid values
            if 0 <= temp <= 50 and 900 <= pressure <= 1100:

                with open("normal_traffic.csv", "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([temp, pressure])

                print("Saved:", temp, pressure)

    except:
        pass


client = mqtt.Client()
client.connect(BROKER, PORT)

client.subscribe("iot/sensor")
client.on_message = on_message

client.loop_forever()