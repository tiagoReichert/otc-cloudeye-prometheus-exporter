FROM python:2.7-alpine

LABEL maintainer "tiago@reichert.eti.br"

COPY requirements.txt /app/

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

RUN apk update
RUN apk add --no-cache openssl
RUN apk add --no-cache bash

ADD ./binary/dockerize-alpine-linux-amd64-v0.6.1.tar.gz /tmp/dockerize-alpine-linux-amd64-v0.6.1.tar.gz
RUN mv /tmp/dockerize-alpine-linux-amd64-v0.6.1.tar.gz/dockerize /usr/local/bin/dockerize \
    && rmdir /tmp/dockerize-alpine-linux-amd64-v0.6.1.tar.gz

COPY ./app /app
COPY ./config /app/config

COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Default variables
ENV REFRESH_TIME 300
ENV LOG_LEVEL INFO
ENV RANCHER_SECRETS false

ENTRYPOINT ["/app/entrypoint.sh"]

