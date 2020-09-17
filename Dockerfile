FROM python:latest

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

WORKDIR /tmp
ADD aionet.py /tmp/aionet.py

RUN useradd appuser && chown -R appuser /tmp
USER appuser

WORKDIR /opt

ENTRYPOINT [ "python", "/tmp/aionet.py" ]