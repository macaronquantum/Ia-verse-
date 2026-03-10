#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y git python3 python3-pip
python3 -m pip install --upgrade pip
python3 -m pip install playwright
echo "Install OpenCrow/OpenCLaw manually according to vendor license if private repository is used."
