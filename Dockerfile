ARG BUILD_FROM=alpine:3.20.5

FROM $BUILD_FROM

ENV TZ="Europe/Rome"

RUN apk update && apk upgrade;\
	apk add --no-cache tzdata minicom nano python3 mosquitto-clients curl py3-pip;\
	python3 -m pip install --no-cache-dir pip --upgrade;\
	pip3 install --no-cache-dir pyserial paho-mqtt requests

COPY *.py .

CMD ["python3", "jeelib_sniffer.py"]
