# Reproducible build of the recovered production backend (sc-workbench:uvr-01-3-7).
# Same steps as backend/Dockerfile, with the base images pinned by digest and every Python
# package pinned to the version installed in the production image (constraints.txt).
FROM julia:1.11.9-bookworm@sha256:51fff9471714bf568780f944af3aebe3b6ea7283d5716b64806713c2f6557a07 AS julia_runtime

FROM python:3.12.15-slim-trixie@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
COPY --from=pins constraints.txt /tmp/constraints.txt
RUN pip install --no-cache-dir -r requirements.txt -c /tmp/constraints.txt && rm /tmp/constraints.txt

COPY . .
RUN chmod +x start.sh

ENV PORT=8088

CMD ["./start.sh"]

COPY --from=julia_runtime /usr/local/julia /usr/local/julia
ENV PATH="/usr/local/julia/bin:${PATH}"
ENV SCWB_JULIA_BIN="/usr/local/julia/bin/julia"
