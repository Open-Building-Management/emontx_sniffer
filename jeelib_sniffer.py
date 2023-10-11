"""read emontx 'jeelib' datas
incoming datas are binary strings
"""
import time
import json
import os
import signal
import serial
import paho.mqtt.client as mqtt

PORT = "/dev/ttyAMA0"
BAUDRATE = 38400
OPTIONS_FILE = "data/options.json"
OPTIONS = {}
if os.path.isfile(OPTIONS_FILE):
    with open(OPTIONS_FILE, encoding="utf-8") as conf:
        OPTIONS = json.loads(conf.read())

def setting(name, default_value):
    """get a user setting from :
    1) the environment
    2) the OPTIONS_FILE
    3) a provided default value"""
    return os.getenv(
        name,
        default=OPTIONS.get(name, default_value)
    )

MQTT_USER = setting("MQTT_USER", "emonpi")
MQTT_PASSWORD = setting("MQTT_PASSWORD", "emonpimqtt2016")
MQTT_HOST = setting("MQTT_HOST", "127.0.0.1").replace("\"", "")
MQTT_PORT = int(setting("MQTT_PORT", "1883"))
VERBOSITY = int(setting("VERBOSITY", True))

def publish_to_mqtt(node, payload):
    """connect to mqtt broker and send payload"""
    message = {}
    message["success"] = True
    try:
        mqttc = mqtt.Client()
        mqttc.username_pw_set(MQTT_USER, password=MQTT_PASSWORD)
        mqttc.connect(MQTT_HOST, port=MQTT_PORT, keepalive=60)
    except Exception as e:
        message["success"] = False
        message["text"] = f'Could not connect to MQTT {e}'
    else:
        text = f'Connected to MQTT and sending to node {node}'
        json_payload = json.dumps(payload)

        result = mqttc.publish(f'emon/{node}', json_payload)
        if result[0] != 0 :
            message["success"] = False
            text = f'{text} Error {result}'
        mqttc.disconnect()
        message["text"] = text
    return message

def read(buf):
    """decode a string where fields are separated by space
    the string should start by "OK", then the node ID
    after it stores all the values as int16 in little endian
    """
    if buf:
        if "\r\n" not in buf.decode():
            print("no end of line received - incomplete packet")
        datas = buf.decode().replace("\r\n", "").strip().split(" ")
        if VERBOSITY:
            print("******************************")
            print(buf)
        if datas[0] == "OK" and len(datas)>=2:
            payload = {}
            rssi = datas[-1].strip()
            if rssi.startswith('(') and rssi.endswith(')'):
                try:
                    payload["rssi"] = int(rssi[1:-1])
                except ValueError:
                    print("rssi is not valid - discarding packet")
                else:
                    frame = [int(i) for i in datas[2:-1]]
                    i=0
                    values=[]
                    while i < len(frame):
                        values.append(int.from_bytes(frame[i:i+2], byteorder = 'little'))
                        i+=2
                    for i, value in enumerate(values):
                        payload[i+1] = value
                    message = publish_to_mqtt(datas[1], payload)
                    if not VERBOSITY:
                        print("******************************")
                    print(message["text"])

def sig_handler(signum, frame):
    """graceful exit the loop"""
    raise SystemExit

def loop():
    """run the loop using a with to connect to serial
    timeout has to be set to 1"""
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    while True:
        try:
            with serial.Serial(PORT, BAUDRATE, timeout=1) as ser:
                rx_buf = ser.readline()
                read(rx_buf)
                ser.close()
        except serial.SerialException as e:
            print(f'error {e}')
            raise SystemExit
        except Exception as e:
            print(f'error {e}')
        time.sleep(0.1)

loop()
