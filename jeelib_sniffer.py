"""read emontx 'jeelib' datas
incoming datas are binary strings
"""
import time
import json
import os
import hashlib
import signal
import logging
import serial
import requests
import paho.mqtt.client as mqtt

SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN", None)
URL = "http://supervisor/core/api/config"
DEST = "/etc/localtime"

FORMAT = "%(asctime)s %(levelname)-8s %(message)s"
logging.basicConfig(format=FORMAT)
log = logging.getLogger()

TARGET_ADDON_GIT_REPO = "https://github.com/Open-Building-Management/emoncms"
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

def get_hash_from_repository(name):
    """Generate a hash from repository."""
    key = name.lower().encode()
    return hashlib.sha1(key).hexdigest()[:8]

PORT = setting("PORT", "/dev/ttyAMA0")
MQTT_USER = setting("MQTT_USER", "emonpi")
MQTT_PASSWORD = setting("MQTT_PASSWORD", "emonpimqtt2016")
MQTT_HOST = setting("MQTT_HOST", f'{get_hash_from_repository(TARGET_ADDON_GIT_REPO)}-emoncms')
MQTT_PORT = int(setting("MQTT_PORT", "1883"))
MQTT_TOPIC = setting("MQTT_TOPIC", "emon/{node}")
VERBOSITY = int(setting("VERBOSITY", True))
RFM69_CONF = setting("RFM69_CONF","15i 200g")
if VERBOSITY:
    log.setLevel("DEBUG")
else:
    log.setLevel("INFO")
info_message = f'MQTT_HOST : {MQTT_HOST} - MQTT_PORT : {MQTT_PORT}'
log.info(info_message)

def connect_to_serial(port, baudrate):
    """open a serial socket"""
    try:
        socket = serial.Serial(port, baudrate, timeout=0)
    except (ValueError, serial.SerialException) as err:
        error_message = f'error {err}'
        log.error(error_message)
        return None
    socket.write(f'{RFM69_CONF}\n'.encode('utf-8'))
    success_message = f'connected to {port}@{baudrate}'
    conf_message=f'Sent configuration:{RFM69_CONF}'
    log.debug(conf_message)
    log.debug(success_message)
    return socket

def on_connect(client, userdata, flags, rc):  # pylint: disable=unused-argument
    """detect the broker response to the connection request"""
    client.connection = True

mqtt.Client.connection = False

def publish_to_mqtt(node, payload):
    """connect to mqtt broker and send payload"""
    message = {}
    message["success"] = True
    mqttc = mqtt.Client()
    mqttc.username_pw_set(MQTT_USER, password=MQTT_PASSWORD)
    mqttc.on_connect = on_connect
    try:
        mqttc.connect(MQTT_HOST, port=MQTT_PORT, keepalive=1)
    except Exception as connexion_error:
        message["success"] = False
        message["text"] = f'Could not connect to MQTT {connexion_error}'
    else:
        mqttc.loop_start()
        while not mqttc.connection :
            time.sleep(0.1)
        result = mqttc.publish(f'MQTT_TOPIC', json.dumps(payload))
        if result[0] != 0 :
            message["success"] = False
        mqttc.disconnect()
        message["text"] = mqtt.connack_string(result[0])
    return message

def read(buf):
    """decode a string where fields are separated by space
    the string should start by "OK", then the node ID
    after it stores all the values as int16 in little endian
    """
    if buf:
        log.debug("******************************")
        log.debug(buf)
        if "\r\n" not in buf.decode():
            log.info("no end of line received - incomplete packet")
        datas = buf.decode().replace("\r\n", "").strip().split(" ")
        if datas[0] == "OK" and len(datas)>=2:
            payload = {}
            rssi = datas[-1].strip()
            if rssi.startswith('(') and rssi.endswith(')'):
                try:
                    payload["rssi"] = int(rssi[1:-1])
                except ValueError:
                    log.error("rssi is not valid - discarding packet")
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
                    if not message["success"]:
                        log.error(message["text"])

class Sniffer:
    """base serial port sniffer through RFM69 devices"""
    def __init__(self):
        self.socket = connect_to_serial(PORT, BAUDRATE)

    def sig_handler(self, signum, frame):  # pylint: disable=unused-argument
        """graceful exit the loop"""
        message = f'received {signum} - exiting'
        log.info(message)
        if self.socket:
            self.socket.close()
        raise SystemExit

    def loop(self):
        """run the loop using a with to connect to serial"""
        signal.signal(signal.SIGINT, self.sig_handler)
        signal.signal(signal.SIGTERM, self.sig_handler)

        while True:
            if self.socket:
                rx_buf = self.socket.readline()
                read(rx_buf)
            else:
                self.socket = connect_to_serial(PORT, BAUDRATE)
            time.sleep(0.1)

if __name__ == "__main__":
    # extracting time zone from the host machine
    container_tz = os.getenv("TZ", default="Europe/Paris")
    try:
        headers = {}
        headers["Authorization"] = f'Bearer {SUPERVISOR_TOKEN}'
        headers["content-type"] = "text/plain"
        conf = requests.get(URL, headers=headers)
    except requests.exceptions.RequestException as requests_error:
        log.error(requests_error)
    else:
        if conf.status_code == 200:
            container_tz = conf.json()["time_zone"]
    finally:
        src = f'/usr/share/zoneinfo/{container_tz}'
        try:
            if os.path.exists(DEST):
                os.remove(DEST)
            os.link(src, DEST)
        except Exception as error:
            log.error(error)
        else:
            info_message = f'timezone {container_tz} fixed'
            log.info(info_message)
    sniffer = Sniffer()
    sniffer.loop()
