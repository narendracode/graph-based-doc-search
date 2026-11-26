#!/usr/bin/env bash
# Bootstraps a fresh Amazon Linux EC2 instance to run the NBCC Archive stack and
# starts it in the background. Idempotent — safe to re-run after a partial failure
# or to redeploy a newer package (every install step checks before installing).
#
# Usage (on the EC2 instance, after extracting the deploy tarball):
#   ./ec2-setup.sh
#
# Assumes: Amazon Linux 2 or 2023, the invoking user has passwordless sudo (the
# EC2 default for ec2-user), and this script is bundled at the root of the
# extracted archive alongside apps/, infra/, Makefile, and .env.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="infra/docker-compose.yml"
ENV_FILE=".env"

log() {
  echo "==> $*"
}

warn() {
  echo "!!  $*" >&2
}

env_get() {
  # Last matching KEY=value line in .env, surrounding quotes and CR stripped.
  # Empty if unset.
  grep -E "^${1}=" "$ENV_FILE" 2>/dev/null | tail -1 \
    | sed -E "s/^${1}=//; s/\r\$//; s/^[\"']//; s/[\"']\$//"
}

set_env_if_default() {
  # Overwrites a value that's still the shipped localhost default, OR that's an
  # auto-generated http://<ip>:<port> from a *previous* run of this script on a
  # different box (e.g. this .env/package got reused on a fresh EC2 instance
  # with a new public IP) — only a genuinely hand-edited value (a custom
  # domain, a non-standard port, https, etc.) is left alone.
  local key="$1" new_value="$2" current
  current="$(env_get "$key")"
  if [[ "$current" =~ ^http://(localhost|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}):[0-9]+$ ]]; then
    sed -i.bak "s#^${key}=.*#${key}=${new_value}#" "$ENV_FILE"
    log "  ${key} -> ${new_value}"
  else
    log "  ${key} already customized (${current}) — leaving as-is"
  fi
}

configure_queue_name() {
  # QUEUE_NAME's shipped default is the bare word "ingestion", not a
  # localhost-shaped value, so this needs its own default-detection rather
  # than reusing set_env_if_default. Must be unique to this deployment: the
  # Redis instance here is shared with local dev (and potentially other EC2
  # boxes) — if two workers listen on the identical queue name, either one can
  # grab a job meant for the other, and try to process a file that only
  # exists on the *other* machine's disk, failing with "no such file".
  local public_ip="$1" current queue_name
  current="$(env_get QUEUE_NAME)"
  if [[ -z "$current" || "$current" == "ingestion" || "$current" =~ ^ingestion-ec2-[0-9]+(-[0-9]+){3}$ ]]; then
    queue_name="ingestion-ec2-${public_ip//./-}"
    if grep -q '^QUEUE_NAME=' "$ENV_FILE"; then
      sed -i.bak "s#^QUEUE_NAME=.*#QUEUE_NAME=${queue_name}#" "$ENV_FILE"
    else
      echo "QUEUE_NAME=${queue_name}" >> "$ENV_FILE"
    fi
    log "  QUEUE_NAME -> ${queue_name}"
  else
    log "  QUEUE_NAME already customized (${current}) — leaving as-is"
  fi
}

dc() {
  sudo docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

# --- 1. OS detection --------------------------------------------------------

detect_os() {
  . /etc/os-release
  OS_ID="${ID:-unknown}"
  OS_VERSION="${VERSION_ID:-unknown}"
  if [[ "$OS_ID" != "amzn" ]]; then
    warn "This script targets Amazon Linux; detected ID=${OS_ID}. Continuing anyway."
  fi
  if [[ "$OS_ID" == "amzn" && "$OS_VERSION" == "2" ]]; then
    warn "Amazon Linux 2 reached end-of-life in June 2026 — Amazon Linux 2023 is recommended."
  fi
  log "Detected OS: ${OS_ID} ${OS_VERSION}"
}

# --- 2. Docker Engine --------------------------------------------------------

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    log "Docker already installed ($(docker --version))"
    return
  fi
  log "Installing Docker Engine..."
  if [[ "$OS_VERSION" == "2023" ]]; then
    sudo dnf install -y docker
  else
    sudo yum install -y amazon-linux-extras
    sudo amazon-linux-extras install docker -y
  fi
}

install_compose_plugin() {
  if sudo docker compose version >/dev/null 2>&1; then
    log "Docker Compose plugin already installed ($(sudo docker compose version))"
    return
  fi
  log "Installing Docker Compose CLI plugin..."
  local arch
  arch="$(uname -m)"
  case "$arch" in
    x86_64) arch="x86_64" ;;
    aarch64) arch="aarch64" ;;
    *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;
  esac
  sudo mkdir -p /usr/local/lib/docker/cli-plugins
  sudo curl -fsSL \
    "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-${arch}" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
}

install_buildx_plugin() {
  # `docker compose ... --build` (and `up --build`) delegates to BuildKit via the
  # buildx CLI plugin as of recent Compose versions ("compose build requires
  # buildx 0.17.0 or later"). Amazon Linux's `docker` package bundles its own
  # (older, insufficient) buildx plugin, so a plain "does `docker buildx
  # version` succeed?" check wrongly reports success against that stale one —
  # always fetch and install the current release instead of trusting that check.
  # Installed into /root/.docker/cli-plugins (every docker call in this script
  # goes through `sudo`, which resets $HOME to root's) since that's the first
  # directory Docker's CLI plugin resolution searches, so it's guaranteed to
  # take precedence over whatever the distro package already bundled.
  log "Installing Docker Buildx CLI plugin..."
  local arch buildx_version release_json_file
  arch="$(uname -m)"
  case "$arch" in
    x86_64) arch="amd64" ;;
    aarch64) arch="arm64" ;;
    *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;
  esac
  # Fetch to a file, then parse the file — piping curl straight into `grep -m1`
  # makes grep close the pipe the instant it finds a match while curl is still
  # writing the rest of the (larger) response, which curl reports as a write
  # error (exit 23) even though the data we wanted already got through; with
  # `pipefail` that false failure aborts the whole script. A plain file has no
  # live producer process for grep's early exit to signal, so this can't
  # happen — a variable is NOT enough here, since piping a large enough string
  # into `grep -m1` can still trip the same SIGPIPE on the writer's end.
  release_json_file="$(mktemp)"
  curl -fsSL https://api.github.com/repos/docker/buildx/releases/latest -o "$release_json_file"
  buildx_version="$(grep -m1 '"tag_name"' "$release_json_file" \
    | sed -E 's/.*"tag_name": *"([^"]+)".*/\1/')"
  rm -f "$release_json_file"
  if [[ -z "$buildx_version" ]]; then
    echo "Couldn't resolve the latest buildx release version" >&2
    exit 1
  fi
  local url="https://github.com/docker/buildx/releases/download/${buildx_version}/buildx-${buildx_version}.linux-${arch}"
  for dir in /root/.docker/cli-plugins /usr/local/lib/docker/cli-plugins; do
    sudo mkdir -p "$dir"
    sudo curl -fsSL "$url" -o "${dir}/docker-buildx"
    sudo chmod +x "${dir}/docker-buildx"
  done

  log "Buildx now resolves to: $(sudo docker buildx version)"
}

start_docker_daemon() {
  sudo systemctl enable --now docker
  # Group membership only takes effect on next login, so the rest of this script
  # uses `sudo docker ...` throughout rather than waiting on it.
  sudo usermod -aG docker "$(whoami)" || true
  for _ in $(seq 1 15); do
    if sudo docker info >/dev/null 2>&1; then
      log "Docker daemon is up"
      return
    fi
    sleep 1
  done
  echo "Docker daemon did not become ready in time" >&2
  exit 1
}

# --- 3. python3 --------------------------------------------------------------

install_python3() {
  if command -v python3 >/dev/null 2>&1; then
    log "python3 already installed ($(python3 --version))"
    return
  fi
  log "Installing python3..."
  if [[ "$OS_VERSION" == "2023" ]]; then
    sudo dnf install -y python3 python3-pip
  else
    sudo yum install -y python3 python3-pip
  fi
}

# --- 4. uv ---------------------------------------------------------------

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    log "uv already installed ($(uv --version))"
    return
  fi
  log "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
}

# --- 5. Ollama -----------------------------------------------------------

install_ollama() {
  if command -v ollama >/dev/null 2>&1; then
    log "Ollama already installed"
  else
    log "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
  fi

  # Ollama's default bind address is 127.0.0.1 — reachable from processes on
  # the host itself, but NOT from inside a Docker container. On Docker
  # Desktop (Mac/Windows), host.docker.internal has special host-forwarding
  # that papers over this; on native Linux Docker Engine (this box),
  # host.docker.internal just resolves to the bridge network's gateway IP, and
  # a service bound only to loopback is unreachable via that path — every
  # api/worker call to Ollama would fail with "connection refused". Binding to
  # 0.0.0.0 instead makes it reachable from the docker bridge too; this is
  # still safe as long as the security group doesn't expose port 11434
  # publicly (it shouldn't). A drop-in, not the main unit file, since
  # Ollama's own installer overwrites ollama.service on every re-run.
  sudo mkdir -p /etc/systemd/system/ollama.service.d
  sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
  sudo systemctl daemon-reload
  sudo systemctl enable --now ollama
  sudo systemctl restart ollama
  for _ in $(seq 1 15); do
    if curl -s -m 2 http://localhost:11434 >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  local embed_model chat_model
  embed_model="$(env_get OLLAMA_EMBED_MODEL)"
  chat_model="$(env_get OLLAMA_CHAT_MODEL)"
  embed_model="${embed_model:-nomic-embed-text}"
  chat_model="${chat_model:-llama3.1:latest}"

  log "Pulling Ollama models (${embed_model}, ${chat_model}) — this downloads several GB and can take a while..."
  ollama pull "$embed_model"
  ollama pull "$chat_model"
}

# --- 6. Point the app at this host's public IP --------------------------

configure_public_host() {
  local token public_ip
  token="$(curl -s -m 2 -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null || true)"
  if [[ -n "$token" ]]; then
    public_ip="$(curl -s -m 2 -H "X-aws-ec2-metadata-token: $token" \
      http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)"
  else
    public_ip="$(curl -s -m 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)"
  fi

  if [[ -z "$public_ip" ]]; then
    warn "Couldn't reach the EC2 metadata service to detect a public IP."
    warn "Edit WEB_ORIGIN and NEXT_PUBLIC_API_URL in ${ENV_FILE} by hand, then re-run this script."
    return
  fi

  log "Detected public IP: ${public_ip}"
  set_env_if_default "WEB_ORIGIN" "http://${public_ip}:3020"
  set_env_if_default "NEXT_PUBLIC_API_URL" "http://${public_ip}:8020"
  configure_queue_name "$public_ip"
}

# --- 7. Build and start the stack -----------------------------------------

start_stack() {
  log "Building and starting the stack in the background..."
  dc up -d --build

  log "Waiting for the API to come up..."
  for _ in $(seq 1 30); do
    if curl -s -m 2 http://localhost:8020/health >/dev/null 2>&1; then
      log "API is healthy"
      break
    fi
    sleep 2
  done

  log "Running migrations..."
  dc exec -T api uv run alembic upgrade head

  log "Seeding initial data..."
  dc exec -T api uv run python -m api.scripts.seed
}

# --- 8. Summary --------------------------------------------------------------

print_summary() {
  local web_origin api_url admin_user
  web_origin="$(env_get WEB_ORIGIN)"
  api_url="$(env_get NEXT_PUBLIC_API_URL)"
  admin_user="$(env_get SUPERADMIN_USERNAME)"

  cat <<EOF

==================================================================
NBCC Archive is up.

  Web:        ${web_origin}
  API docs:   ${api_url}/docs
  Login:      ${admin_user:-admin} / (SUPERADMIN_PASSWORD in ${ENV_FILE}) — change it.

IMPORTANT: this only starts the app on the box. Your EC2 security group must
separately allow inbound traffic on ports 3020 and 8020 (and 22 for SSH) for
anyone to actually reach it — this script can't change that for you.

Useful commands (from ${SCRIPT_DIR}):
  sudo docker compose --env-file .env -f ${COMPOSE_FILE} ps
  sudo docker compose --env-file .env -f ${COMPOSE_FILE} logs -f
  sudo docker compose --env-file .env -f ${COMPOSE_FILE} down
==================================================================
EOF
}

main() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "No ${ENV_FILE} found next to this script — was the archive extracted correctly?" >&2
    exit 1
  fi

  detect_os
  install_docker
  install_compose_plugin
  install_buildx_plugin
  start_docker_daemon
  install_python3
  install_uv
  install_ollama
  configure_public_host
  start_stack
  print_summary
}

main "$@"
