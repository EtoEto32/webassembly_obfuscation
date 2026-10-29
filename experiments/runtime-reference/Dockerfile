FROM debian:bookworm-slim@sha256:7c7b2c966bc9ee8cedfeef67e0e279108992c77681fa595db4a9d65c06ccc587
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver python3 python3-selenium python3-flask nodejs ca-certificates musl \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 experiment
COPY smoke.py /opt/experiment/smoke.py
COPY node_modules /opt/runtime-node/node_modules
USER experiment
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_PATH=/opt/runtime-node/node_modules
ENTRYPOINT ["python3", "/opt/experiment/smoke.py"]
