FROM julia:1.11-bookworm AS julia_runtime

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

ENV PORT=8088

CMD ["./start.sh"]

COPY --from=julia_runtime /usr/local/julia /usr/local/julia
ENV PATH="/usr/local/julia/bin:${PATH}"
ENV SCWB_JULIA_BIN="/usr/local/julia/bin/julia"
