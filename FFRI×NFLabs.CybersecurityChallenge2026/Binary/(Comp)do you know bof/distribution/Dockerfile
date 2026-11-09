FROM ubuntu:24.04

RUN apt update && \
    apt install -y --no-install-recommends socat && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /chall

COPY chall ./

CMD ["socat", "TCP-L:4000,reuseaddr,fork", "EXEC:./chall"]