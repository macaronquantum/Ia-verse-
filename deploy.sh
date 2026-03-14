#!/bin/bash

set -e

echo "Pulling latest code..."
git pull origin main

echo "Rebuilding containers..."
docker compose down
docker compose up -d --build

echo "Deployment complete"
