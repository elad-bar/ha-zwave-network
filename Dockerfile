FROM python:latest

COPY . /

ENV HA_URL ""
ENV HA_TOKEN ""
ENV SSL_KEY ""
ENV SSL_CERTIFICATE ""

RUN pip install requests

EXPOSE 6123

ENTRYPOINT ["python3", "webserver.py"]