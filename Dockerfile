FROM alpine:3.21

RUN apk update && \
    apk add --no-cache \
        python3 \
        py3-pip \
        bash \
        tini && \
    python3 -m pip config set global.break-system-packages true && \
    rm -rf /var/cache/apk/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

COPY . /app/
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/app/entrypoint.sh"]
