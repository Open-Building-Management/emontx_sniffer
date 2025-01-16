ARG BUILD_FROM=alpine:3.21.2

FROM $BUILD_FROM

ENV \
    PATH="/ve/bin:$PATH" \
    TZ="Europe/Rome"

RUN apk update && apk upgrade;\
	apk add --no-cache tzdata minicom nano python3 mosquitto-clients curl py3-pip pipx;\
	python3 -m pip install --no-cache-dir pip --upgrade;\
 	python3 -m venv /ve;\
        . /ve/bin/activate;\
 	pip3 install --no-cache-dir pyserial paho-mqtt requests
COPY *.py .
CMD ["python3", "jeelib_sniffer.py"]
