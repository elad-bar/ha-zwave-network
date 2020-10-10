FROM python:3.8-alpine

COPY . /

ENV HA_URL ""
ENV HA_TOKEN ""
ENV SSL_KEY ""
ENV SSL_CERTIFICATE ""

RUN apk update && \
    apk upgrade && \
    apk add nano && \
    pip install requests && \
    pip install asyncws

EXPOSE 6123

ENTRYPOINT ["python3", "webserver.py"]