#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y software-properties-common curl gnupg ca-certificates lsb-release git build-essential redis-server postgresql postgresql-contrib python3.11 python3.11-venv python3-pip

if ! command -v docker >/dev/null; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

if ! command -v node >/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

if command -v nvidia-smi >/dev/null; then
  sudo apt-get install -y nvidia-cuda-toolkit
fi

if ! command -v ollama >/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

sudo systemctl enable --now redis-server || true
sudo systemctl enable --now postgresql || true
sudo usermod -aG docker "$USER" || true

echo "Server setup complete. Re-login to apply docker group permissions."
