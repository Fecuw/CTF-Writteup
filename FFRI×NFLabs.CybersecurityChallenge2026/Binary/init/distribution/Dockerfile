FROM ubuntu:26.04
WORKDIR /app

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    socat \
    && rm -rf /var/lib/apt/lists/*

COPY ./init .
COPY ./flag.txt .

CMD ["socat", "TCP-LISTEN:24634,reuseaddr,fork", "EXEC:'./init'"]
