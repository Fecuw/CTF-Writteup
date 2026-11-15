FROM ubuntu:24.04

RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libc6:i386 \
        socat && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /pwn

COPY parrot /pwn/parrot
COPY parrots_memory.txt /pwn/parrots_memory.txt

RUN useradd --create-home --shell /usr/sbin/nologin pwn && \
    chown root:root /pwn/parrot /pwn/parrots_memory.txt && \
    chmod 755 /pwn/parrot && \
    chmod 444 /pwn/parrots_memory.txt

USER pwn

EXPOSE 24002

CMD ["socat", "TCP-LISTEN:24002,reuseaddr,fork", "EXEC:/pwn/parrot,stderr"]