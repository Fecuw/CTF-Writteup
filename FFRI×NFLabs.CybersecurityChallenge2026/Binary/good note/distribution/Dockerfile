FROM ubuntu:24.04

RUN apt update && \
    apt install -y --no-install-recommends socat && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /good_note

COPY good_note ./

CMD ["socat", "TCP-L:4000,reuseaddr,fork", "EXEC:./good_note"]
