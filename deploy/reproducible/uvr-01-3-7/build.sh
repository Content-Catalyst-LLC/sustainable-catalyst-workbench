#!/usr/bin/env bash
# Build the recovered backend reproducibly and check the installed packages against the pins.
# Usage: deploy/reproducible/uvr-01-3-7/build.sh <image tag>
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); root=$(cd "$here/../../.." && pwd)
tag=${1:?image tag}
docker build -f "$here/Dockerfile" --build-context pins="$here" -t "$tag" "$root/backend"
docker run --rm --network none --entrypoint pip "$tag" freeze --all | grep -v '^pip==' | LC_ALL=C sort > "$here/.installed.txt"
if LC_ALL=C sort "$here/constraints.txt" | diff - "$here/.installed.txt"; then
  echo "installed packages match constraints.txt"
else
  echo "installed packages differ from constraints.txt" >&2; exit 1
fi
rm -f "$here/.installed.txt"
