#!/usr/bin/env bash
set -euo pipefail

ollama pull mistral
ollama pull mixtral
ollama pull llama3
ollama pull codellama

echo "Local models installed."
