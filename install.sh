#!/usr/bin/env bash
# install.sh — Installe (ou met à jour) noblogs-backup-lite, puis lance l'outil.
#
# Utilisations (Linux / macOS / Tails) :
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)"
#   bash -c "$(wget  -qO- https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)"
#   # sauvegarde directe d'un blog :
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.sh)" -- sauvegarder monblog
set -euo pipefail

# --------------------------------------------------------------- couleurs
if [ -t 1 ]; then
  G="\033[0;32m"; R="\033[0;31m"; Y="\033[1;33m"; C="\033[0;36m"; N="\033[0m"
else
  G=""; R=""; Y=""; C=""; N=""
fi
ok()   { echo -e "  ${G}✓${N} $*"; }
warn() { echo -e "  ${Y}!${N} $*"; }
err()  { echo -e "  ${R}✗${N} $*" >&2; }
info() { echo -e "  ${C}→${N} $*"; }

# ------------------------------------------------------------------ langue
USER_LANG="${LANG:-}"
if [[ "$USER_LANG" == en* ]]; then
  L_TITLE="Installing noblogs-backup-lite…"
  L_NO_TOOL="Download impossible: curl/wget unavailable or no network."
  L_PY_DIR="Install directory:"
  L_TAG="Downloading version v2.1.0…"
  L_MAIN="v2.1.0 not found, using latest main…"
  L_BAD="Downloaded archive is invalid."
  L_OK="Installed"
  L_UPDATE="Updated"
  L_RUN="Launching"
  L_ANON="Tip: for anonymity, reboot into Tails (https://tails.net) — all traffic goes through Tor."
  L_ERROR="Installation failed."
elif [[ "$USER_LANG" == it* ]]; then
  L_TITLE="Installazione di noblogs-backup-lite…"
  L_NO_TOOL="Download impossibile: curl/wget non disponibili o nessuna rete."
  L_PY_DIR="Directory di installazione:"
  L_TAG="Download versione v2.1.0…"
  L_MAIN="v2.1.0 non trovata, uso l'ultima main…"
  L_BAD="L'archivio scaricato non è valido."
  L_OK="Installato"
  L_UPDATE="Aggiornato"
  L_RUN="Avvio"
  L_ANON="Suggerimento: per l'anonimato, riavvia in Tails (https://tails.net) — tutto il traffico passa per Tor."
  L_ERROR="Installazione fallita."
else
  L_TITLE="Installation de noblogs-backup-lite…"
  L_NO_TOOL="Téléchargement impossible : curl/wget absents ou pas de réseau."
  L_PY_DIR="Répertoire d'installation :"
  L_TAG="Téléchargement de la version v2.1.0…"
  L_MAIN="v2.1.0 introuvable, bascule sur la dernière main…"
  L_BAD="L'archive téléchargée est invalide."
  L_OK="Installé"
  L_UPDATE="Mis à jour"
  L_RUN="Lancement"
  L_ANON="Astuce : pour l'anonymat, redémarrez sous Tails (https://tails.net) — tout le trafic passe par Tor."
  L_ERROR="Échec de l'installation."
fi

# ----------------------------------------------------------- plateforme
detect_platform() {
  if [ -f /etc/amnesia ] || [ -n "${TAILS_VERSION:-}" ] || grep -qi 'ID=tails' /etc/os-release 2>/dev/null; then
    echo "tails"
  elif [ "$(uname -s)" = "Darwin" ]; then
    echo "macos"
  else
    echo "linux"
  fi
}

target_dir() {
  local plat
  plat="$(detect_platform)"
  if [ "$plat" = "tails" ] && [ -d "${HOME}/Persistent" ]; then
    echo "${HOME}/Persistent/noblogs-backup-lite"
  else
    echo "${HOME}/noblogs-backup-lite"
  fi
}

# ------------------------------------------------------------------ téléchargement
download() {  # $1=url  → stdout
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$1" 2>/dev/null || wget -qO- "$1" 2>/dev/null || return 9
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$1" 2>/dev/null || return 9
  else
    return 9
  fi
}

TAG_URL="https://codeload.github.com/muarf/noblogs-backup-lite/tar.gz/refs/tags/v2.1.0"
MAIN_URL="https://codeload.github.com/muarf/noblogs-backup-lite/tar.gz/refs/heads/main"

# ---------------------------------------------------------------- install
main() {
  echo ""
  info "$L_TITLE"
  echo ""

  TARGET="$(target_dir)"
  info "$L_PY_DIR $TARGET"

  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT

  info "$L_TAG"
  if ! download "$TAG_URL" > "$TMP/archive.tgz" 2>/dev/null; then
    info "$L_MAIN"
    if ! download "$MAIN_URL" > "$TMP/archive.tgz" 2>/dev/null; then
      err "$L_NO_TOOL"
      exit 1
    fi
  fi

  if [ "$(wc -c < "$TMP/archive.tgz")" -lt 5000 ]; then
    err "$L_BAD"
    exit 1
  fi

  mkdir -p "$TMP/src"
  if ! tar -xzf "$TMP/archive.tgz" -C "$TMP/src"; then
    err "$L_BAD"
    exit 1
  fi

  SRC="$(find "$TMP/src" -maxdepth 1 -type d -name 'noblogs-backup-lite-*' | head -1)"
  if [ -z "$SRC" ] || [ ! -x "$SRC/noblogs" ] || [ ! -f "$SRC/requirements.txt" ]; then
    err "$L_BAD"
    exit 1
  fi

  mkdir -p "$TARGET"
  # Mise à jour non-destructive : on copie le code par-dessus, en préservant
  # backups/ et .venv/ existants.
  cp -a "$SRC/." "$TARGET/"
  chmod +x "$TARGET/noblogs" 2>/dev/null || true

  if [ -d "$TARGET/.venv" ] && [ -x "$TARGET/.venv/bin/python3" ]; then
    ok "$L_UPDATE"
  else
    ok "$L_OK"
  fi

  if [ "$(detect_platform)" != "tails" ]; then
    warn "$L_ANON"
    echo ""
  fi

  info "$L_RUN noblogs…"
  echo ""
  cd "$TARGET"
  exec ./noblogs "$@"
}

main "$@"