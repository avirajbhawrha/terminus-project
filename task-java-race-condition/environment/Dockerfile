FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest

WORKDIR /app

COPY app/ /app/

RUN mkdir -p /app/output

CMD ["/bin/bash"]
