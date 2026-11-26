#!/usr/bin/env bash
# Packages the NBCC Archive project into a self-contained tarball ready to `scp`
# to an EC2 instance and run. Includes the real .env (same shared dev
# Postgres/Redis/Neo4j credentials already used locally) plus scripts/ec2-setup.sh
# (placed at the archive root) which installs everything needed and starts the
# stack in the background.
#
# Usage (from the repo root):
#   ./scripts/package-for-ec2.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f ".env" ]]; then
  echo "No .env found at the repo root — copy .env.example to .env and fill it in first." >&2
  exit 1
fi

TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
ARCHIVE_NAME="nbcc-archive-deploy-${TIMESTAMP}.tar.gz"
STAGE_DIR="$(mktemp -d)"
PKG_DIR="${STAGE_DIR}/nbcc-archive"

cleanup() {
  rm -rf "$STAGE_DIR"
}
trap cleanup EXIT

echo "==> Staging package contents..."
mkdir -p "$PKG_DIR"

rsync -a \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '*.pyc' \
  apps/api "$PKG_DIR/apps/"

rsync -a \
  --exclude 'node_modules' \
  --exclude '.next' \
  apps/web "$PKG_DIR/apps/"

mkdir -p "$PKG_DIR/infra"
cp infra/docker-compose.yml "$PKG_DIR/infra/"
cp Makefile "$PKG_DIR/"
cp README.md "$PKG_DIR/"
cp .env "$PKG_DIR/"
cp scripts/ec2-setup.sh "$PKG_DIR/"
chmod +x "$PKG_DIR/ec2-setup.sh"

# Reset deployment-specific values in the STAGED .env copy back to their
# shipped defaults — never touches the real local .env. Local dev's own .env
# may have already been customized (e.g. QUEUE_NAME=ingestion-local, so this
# machine's worker doesn't collide with a deployed one on the same shared
# Redis) — shipping those values verbatim would silently defeat
# ec2-setup.sh's "only configure it if it's still the default" checks on
# whatever box this package lands on, since a non-default value looks
# already-configured. Resetting here means a fresh package is always safe to
# extract onto a new box, regardless of what state local .env is in when it's
# built.
sed -i.bak \
  -e 's#^WEB_ORIGIN=.*#WEB_ORIGIN=http://localhost:3020#' \
  -e 's#^NEXT_PUBLIC_API_URL=.*#NEXT_PUBLIC_API_URL=http://localhost:8020#' \
  -e 's#^QUEUE_NAME=.*#QUEUE_NAME=ingestion#' \
  "$PKG_DIR/.env"
rm -f "$PKG_DIR/.env.bak"

echo "==> Creating ${ARCHIVE_NAME}..."
tar czf "${REPO_ROOT}/${ARCHIVE_NAME}" -C "$STAGE_DIR" nbcc-archive

SIZE="$(du -h "${REPO_ROOT}/${ARCHIVE_NAME}" | cut -f1)"

cat <<EOF

==================================================================
Package ready: ${ARCHIVE_NAME} (${SIZE})

This archive contains a working .env with live credentials for the shared dev
Postgres/Redis/Neo4j instances. That's fine to send over scp (SSH is already
encrypted), but don't leave copies of it lying around or commit it anywhere.

Next steps:

  1. Copy it to your EC2 instance:
       scp -i /path/to/your-key.pem ${ARCHIVE_NAME} ec2-user@<your-ec2-host>:~

  2. On the EC2 instance, extract and run the setup script:
       tar xzf ${ARCHIVE_NAME}
       cd nbcc-archive
       ./ec2-setup.sh

  This installs Docker, uv, python3, and Ollama if missing, points the app at
  this instance's public IP, and brings the stack up in the background. It's
  safe to re-run if it's interrupted partway through.

  Remember: the instance's security group must separately allow inbound
  traffic on ports 3020 and 8020 for anyone outside to reach it.
==================================================================
EOF
