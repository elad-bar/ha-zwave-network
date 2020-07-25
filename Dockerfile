FROM python:latest

COPY . /

EXPOSE 6123

ENTRYPOINT ["/bin/bash", "entry_point.sh"]