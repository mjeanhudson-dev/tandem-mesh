#!/usr/bin/env bash
# ==============================================================================
# Synchronize build artifacts to staging directory
# Use case: automated deployment pipeline and nightly test harness runs
# ==============================================================================

set -euo pipefail

sync_artifacts() {
    local src="$1"
    local dst="$2"
    echo "Syncing $src to $dst"
    rsync -avz "$src/" "$dst/"
}

sync_artifacts "$@"
