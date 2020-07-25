FROM python:latest

COPY index.html /

EXPOSE 6123

CMD python3 -m http.server 6123