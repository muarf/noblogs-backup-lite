#!/usr/bin/env bash
# noblogs.command — Lanceur macOS double-clic pour noblogs-backup.
cd "$(dirname "$0")"
exec ./noblogs "$@"