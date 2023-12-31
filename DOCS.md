This tool reads radio data coming from emontx and send them to the emoncms

You need a RFM69 radio receiver :

- either one attached to the GPIO, like [emonPi](https://docs.openenergymonitor.org/emonpi/index.html) or [RFM69Pi](https://docs.openenergymonitor.org/emonbase/rfm69-pi.html) 

- either a USB one, like the [jeelink-rfm69cw-to-usb-transceiver-433mhz](https://shop.openenergymonitor.com/jeelink-rfm69cw-to-usb-transceiver-433mhz/)

# usage with a radio receiver attached to the GPIO

![emonbase](https://github.com/Open-Building-Management/emontx_sniffer/raw/main/images/emonbase.png)

Devices connected to the GPIO are usually recognized as `/dev/ttyAMA0`, the same port used by bluetooth on a raspberry

Disabling bluetooth requires to modify `/boot/config.txt` and to add the following lines at the end :
```
[all]
dtoverlay=disable-bt
```
On a classic raspbian OS, it is easy as `/boot` is mounted if you read your SD card on a linux machine

If running an factory [SD card](https://www.home-assistant.io/installation/raspberrypi#writing-the-image-with-balena-etcher) using [buildroot](https://buildroot.org/), things are a bit different.

It will require to establish an SSH access to the host through port 22222, as explained [here](https://developers.home-assistant.io/docs/operating-system/debugging/)

Once connected with `ssh root@homeassistant.local -p 22222`, edit `/mnt/boot/config.txt`

# debugging the serial port

If you are using a RFM69 which you do not remember having reconfigured, you can have some troubles like receiving packets like that :
```
? G0 29 79 85 208 241 51 133 87 172 22 78 60 96 83 74 211 194 51 60 114 242 (-98)
```
**Stop the add-on,** open an SSH session and run a docker container with access to `/dev/ttyAMA0` :
```
docker run --rm --device=/dev/ttyAMA0 -it alexjunk/emontx_sniffer:alpine3.18 sh
```
Open a minicom session with `minicom -b38400 -D/dev/ttyAMA0`

Press `v` to check the version device and if it returns something like : `E i5 g0 @ 433MHz`, you are on group `0` and cannot sniff openenergymonitor devices which are using group `210` when they send radio packets

To correct, press `210g` + `return` to change the group to `210`

You can quit minicom with `CTRL-A` + `Q`, exit the container and restart the addon

# testing MQTT

If there is no incoming data in emoncms, you should check the add-on configuration, so that the credentials fit to the emoncms add-on configuration. 

It is possible to test the mqtt connectivity in command line and it does not require to stop the addon.

Start by listing all running containers with `docker container ls` and identify the emontx_sniffer among them :
```
CONTAINER ID   IMAGE
12345546d715   alexjunk/emontx_sniffer:alpine3.18
292137d2a0d9   homeassistant/armv7-addon-configurator:5.6.0
```
Open a shell session to the running container with `docker exec -it 12345546d715 sh` and run the `mqtt_test.py` script
```
# python3 mqtt_test.py 
{'success': True, 'text': 'Connection Accepted.'}
```
