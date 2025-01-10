ARG BUILD_FROM=alpine:3.21.2

FROM $BUILD_FROM

ARG \
  ENV_DIR=/ve

RUN apk update && apk upgrade;\
  apk add --no-cache tzdata minicom nano python3 mosquitto-clients curl;\
  apk add --no-cache py3-pip py3-virtualenv;\
  python3 -m venv $ENV_DIR;\
  $ENV_DIR/bin/pip install --no-cache-dir pyserial paho-mqtt requests

COPY *.py .

ENV \
  PATH="{$ENV_DIR}/bin:$PATH" \
  TZ="Europe/Paris"

CMD ["python3", "jeelib_sniffer.py"]
