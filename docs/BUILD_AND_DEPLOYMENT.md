# Workbench ARM64 Development Runbook

## Verified development environment

- Raspberry Pi 4, Debian 12, ARM64
- Branch: fix/workbench-v10110-reproducibility
- Recovery commit: 58ef258
- Docker image: catalyst-workbench-repair:7x
- Container: catalyst-workbench-repair-7y
- Host binding: 127.0.0.1:8088
- Container port: 8088

This is a local development environment, not production.

## Repository

/mnt/catalyst-ssd/repositories/sustainable-catalyst-workbench

Before development, verify SSD health:

sudo /usr/local/sbin/check-catalyst-ssd

## Build

From the repository root:

sudo docker build \
  --platform linux/arm64 \
  -f backend/Dockerfile \
  -t catalyst-workbench-repair:7x \
  backend

The build context must be backend, not the repository root.

## Start

Only if the named container does not already exist:

sudo docker run -d \
  --name catalyst-workbench-repair-7y \
  --network bridge \
  -p 127.0.0.1:8088:8088 \
  catalyst-workbench-repair:7x

Never publish development ports on 0.0.0.0
without a separate access-control review.

## Health verification

curl -fsS http://127.0.0.1:8088/openapi.json

## Application logs

sudo docker logs --tail 100 \
  catalyst-workbench-repair-7y

## Stop

sudo docker stop catalyst-workbench-repair-7y

## Restart

sudo docker start catalyst-workbench-repair-7y

## Testing

The recovery-specific certification and integrity
suite passed 13 tests on 2026-10-26.

See docs/VERIFICATION_RESULTS.md.

## Rollback

The original image remains tagged:

catalyst-workbench-dev-workbench

Do not delete the original image.

Stop the repair container before attempting an
alternative deployment on the same host port.

## Production

No production deployment is authorized by this runbook.

The reconstructed v10.11 module requires additional
compatibility review before production release.
