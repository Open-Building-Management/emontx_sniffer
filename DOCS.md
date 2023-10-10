This tool reads radio data coming from emontx and send them to the emoncms

# usage with a radio receiver attached to the GPIO

[emonbase](images/emonbase.png)

Such a device, like emonpi or RFM69Pi will be recognized as `/dev/ttyAMA0`, the same port used by bluetooth on a raspberry

Disabling bluetooth requires to modify `/boot/config.txt` and to add the following lines at the end :
```
[all]
dtoverlay=disable-bt
```
On a classic raspbian OS, it is easy as `/boot` is mounted if you read your SD card on a linux machine

If running an factory [SD card](https://www.home-assistant.io/installation/raspberrypi#writing-the-image-with-balena-etcher), things are a bit different.

It will require to establish an SSH access to the host through port 22222 !

Click [here](https://developers.home-assistant.io/docs/operating-system/debugging/) to see how to achieve this

Once connected with `ssh root@homeassistant.local -p 22222`, edit `/mnt/boot/config.txt`

# usage with a USB dongle

Not implemented yet
