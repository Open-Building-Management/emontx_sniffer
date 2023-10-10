ARG BUILD_FROM=alpine:3.16

FROM BUILD_FROM

ENV TZ="Europe/Paris"

RUN apk update && apk upgrade;\
	apk add --no-cache tzdata nano python3 py3-pip;\
	python3 -m pip install --no-cache-dir pip --upgrade;\
	pip3 install --no-cache-dir pyserial paho-mqtt

COPY jeelib_sniffer.py .

CMD ["python3", "jeelib_sniffer.py"]
