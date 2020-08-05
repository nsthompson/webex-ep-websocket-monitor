FROM python:3.8.3-slim-buster

LABEL maintainer="@nsthompson"

WORKDIR /src

RUN apt-get update && apt-get install -qq -y \
    build-essential \
    libpq-dev --no-install-recommends

COPY . /src
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED='true'

CMD ['python3', 'websocket-monitor.py']