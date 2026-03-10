#!/usr/bin/env bash
set -euo pipefail
mkdir -p backups
docker exec ia-verse-postgres pg_dump -U iaverse ia_verse > "backups/ia_verse_$(date +%Y%m%d_%H%M%S).sql"
