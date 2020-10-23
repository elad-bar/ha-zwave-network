FROM python:3.9-alpine

ENV HA_URL ""
ENV HA_TOKEN ""
ENV SSL_KEY ""
ENV SSL_CERTIFICATE ""
ENV SERVER_PORT 6123
ENV DEBUG false
ENV LOCAL false

RUN apk update && \
    apk upgrade && \
    apk add --no-cache gcc libressl-dev musl-dev libffi-dev nano && \
    pip install requests && \
    pip install asyncws && \
    pip install aiofiles && \
    pip install flask && \
    pip install pyopenssl

COPY . /app/

VOLUME [ "/debug" ]

EXPOSE 6123

ENTRYPOINT ["python3", "/app/webserver.py"]