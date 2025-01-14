ARG BUILD_FROM=alpine:3.20.5

FROM $BUILD_FROM

ENV TZ="Europe/Rome"

RUN apk update && apk upgrade;\
	apk add --no-cache tzdata minicom nano python3 mosquitto-clients curl py3-pip pipx;\
	python3 -m pip install --no-cache-dir pip --upgrade;\
	pipx install  pyserial paho-mqtt requests;\
 	cp jeelib_sniffer.py /ve;\
 	python3 -m venv /ve;\
        . /ve/bin/activate;\
 	/ve/bin/pip3 install --no-cache-dir paho-mqtt

CMD ["/ve/bin/python3", "/jeelib_sniffer.py"]
