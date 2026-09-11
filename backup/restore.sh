#!/bin/bash
# ============================================================================
# restore.sh — Restauration complète d'un backup NoBlogs sur WordPress
#
# Usage :
#   ./restore.sh                              # mode interactif
#   WP=/var/www/html ./restore.sh             # dossier WordPress cible
#   WP=/var/www/html URL=https://x.fr ./restore.sh  # avec remplacement d'URL
#   WP=/var/www/html SKIP_WXR=1 ./restore.sh  # sauter l'import WXR (si déjà fait)
#
# Prérequis : WordPress installé (wp-load.php présent), WP-CLI recommandé.
# ============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

WP="${WP:-./wordpress}"
URL="${URL:-}"
SKIP_WXR="${SKIP_WXR:-0}"
DB="${DB:-}"
SLUG=""

# --- Couleurs ---
G="\033[0;32m" ; R="\033[0;31m" ; Y="\033[1;33m" ; C="\033[0;36m" ; N="\033[0m"
ok()   { echo -e "${G}[OK]${N} $*"; }
warn() { echo -e "${Y}[!]${N} $*"; }
err()  { echo -e "${R}[ERR]${N} $*"; }
info() { echo -e "${C}[i]${N} $*"; }

# --- Détection slug ---
if [ -f "$SCRIPT_DIR/metadata.json" ]; then
    SLUG=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/metadata.json'))['slug'])" 2>/dev/null || true)
fi
if [ -z "$SLUG" ]; then
    SLUG=$(basename "$SCRIPT_DIR" | sed 's/-noblogs-backup$//')
fi

if [ ! -f "$WP/wp-load.php" ]; then
    err "WordPress non trouvé dans $WP (wp-load.php absent)."
    echo "  Usage : WP=/var/www/html ./restore.sh"
    exit 1
fi

if ! command -v wp &>/dev/null; then
    warn "WP-CLI non trouvé. L'import WXR et les opérations DB seront manuelles."
fi

echo ""
echo -e "${C}══════════════════════════════════════════════════════════════${N}"
echo -e "${C}  Restauration du blog ${SLUG:-?}  →  ${WP}${N}"
echo -e "${C}══════════════════════════════════════════════════════════════${N}"
echo ""

# ========================== 1. MEDIAS =======================================
echo -e "${C}1/7  Médias (uploads/)${N}"
if [ -d "$SCRIPT_DIR/uploads" ] && [ "$(ls -A "$SCRIPT_DIR/uploads" 2>/dev/null)" ]; then
    mkdir -p "$WP/wp-content/uploads"
    cp -rn "$SCRIPT_DIR/uploads/." "$WP/wp-content/uploads/"
    ok "Médias copiés dans wp-content/uploads/"
elif [ -d "$SCRIPT_DIR/fidelity_media" ] && [ "$(ls -A "$SCRIPT_DIR/fidelity_media" 2>/dev/null)" ]; then
    # Secours : au minimum la bannière / logo / fond extraits avec la fidélité
    mkdir -p "$WP/wp-content/uploads"
    cp -rn "$SCRIPT_DIR/fidelity_media/." "$WP/wp-content/uploads/"
    ok "Médias fidélité copiés dans wp-content/uploads/ (backup réduit)"
else
    warn "Aucun média à copier."
fi

# ========================== 2. THEME ========================================
echo -e "${C}2/7  Thème${N}"
if [ -d "$SCRIPT_DIR/theme" ]; then
    THEME_DIR=$(ls -d "$SCRIPT_DIR/theme"/*/ 2>/dev/null | head -1)
    if [ -n "$THEME_DIR" ]; then
        THEME_NAME=$(basename "$THEME_DIR")
        mkdir -p "$WP/wp-content/themes"
        cp -r "$THEME_DIR" "$WP/wp-content/themes/$THEME_NAME"
        ok "Thème '$THEME_NAME' copié dans wp-content/themes/"
        if command -v wp &>/dev/null; then
            wp theme activate "$THEME_NAME" --path="$WP" --allow-root 2>/dev/null && \
                ok "Thème '$THEME_NAME' activé" || \
                warn "Activation du thème échouée — activez-le manuellement."
        fi
    else
        warn "Aucun dossier thème trouvé dans theme/"
    fi
else
    warn "Dossier theme/ absent — le thème par défaut restera actif."
fi

# ========================== 3. IMPORT WXR ===================================
echo -e "${C}3/7  Import WXR (articles + pages)${N}"
if [ "$SKIP_WXR" = "1" ]; then
    info "Import WXR ignoré (SKIP_WXR=1)."
elif [ -f "$SCRIPT_DIR/wordpress-export.xml" ]; then
    if command -v wp &>/dev/null; then
        wp plugin is-active wordpress-importer --path="$WP" --allow-root >/dev/null 2>&1 || \
            wp plugin install wordpress-importer --activate --path="$WP" --allow-root 2>/dev/null || true
        wp import "$SCRIPT_DIR/wordpress-export.xml" --authors=create --path="$WP" --allow-root 2>&1 | tail -5
        ok "Import WXR terminé."
    else
        warn "WP-CLI absent — importez 'wordpress-export.xml' via Outils > Importer > WordPress."
    fi
else
    err "wordpress-export.xml non trouvé."
fi

# ========================== 4. URL REPLACEMENT ==============================
echo -e "${C}4/7  Remplacement des URLs${N}"
if [ -n "$URL" ] && command -v wp &>/dev/null; then
    ORIGINAL_URL=""
    if [ -f "$SCRIPT_DIR/metadata.json" ]; then
        ORIGINAL_URL=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/metadata.json')).get('original_url',''))" 2>/dev/null || true)
    fi
    if [ -n "$ORIGINAL_URL" ]; then
        wp search-replace "$ORIGINAL_URL" "$URL" --all-tables --path="$WP" --allow-root 2>/dev/null && \
            ok "URLs remplacées : $ORIGINAL_URL → $URL" || \
            warn "Remplacement partiel — vérifiez les URLs manuellement."
    else
        warn "URL d'origine inconnue — pas de remplacement automatique."
    fi
else
    if [ -z "$URL" ]; then
        info "Pas de remplacement d'URL (URL non défini)."
    fi
fi

# ========================== 5. PARITY (widgets, menus, CSS) =================
echo -e "${C}5/7  Fidélité visuelle (widgets, menus, CSS, couleurs)${N}"
if [ -f "$SCRIPT_DIR/fidelity.json" ] && command -v wp &>/dev/null; then
    if [ -f "$SCRIPT_DIR/restore_parity.php" ]; then
        wp eval-file "$SCRIPT_DIR/restore_parity.php" --path="$WP" --allow-root 2>&1 | head -20
        ok "Fidélité visuelle appliquée."
    else
        warn "restore_parity.php absent — fidélité non appliquée."
    fi
else
    if [ ! -f "$SCRIPT_DIR/fidelity.json" ]; then
        info "fidelity.json absent — pas de fidélité à appliquer."
    fi
fi

# ========================== 6. MORE TAGS ====================================
echo -e "${C}6/7  Balises <!--more-->${N}"
if command -v wp &>/dev/null; then
    cat > "$SCRIPT_DIR/_restore_more.sql" << 'SQL'
UPDATE wp_posts SET post_content = REGEXP_REPLACE(post_content, '<p><span id="more-[0-9]+"></span></p>', '<!--more-->');
UPDATE wp_posts SET post_content = REGEXP_REPLACE(post_content, '<span id="more-[0-9]+"></span>', '<!--more-->');
UPDATE wp_posts SET post_content = REGEXP_REPLACE(post_content, '<p><!--more--></p>', '<!--more-->');
SQL
    if wp db query < "$SCRIPT_DIR/_restore_more.sql" --path="$WP" --allow-root 2>/dev/null; then
        ok "Tags <!--more--> restaurés."
    else
        warn "Échec restauration more (base incompatible REGEXP_REPLACE)."
    fi
    rm -f "$SCRIPT_DIR/_restore_more.sql"
fi

# ========================== 7. FINAL CLEANUP ================================
echo -e "${C}7/7  Nettoyage final${N}"
if command -v wp &>/dev/null; then
    wp rewrite flush --path="$WP" --allow-root 2>/dev/null
    wp cache flush --path="$WP" --allow-root 2>/dev/null
    wp post delete 1 2 --force --path="$WP" --allow-root 2>/dev/null || true
    wp option update use_balanceTags 1 --path="$WP" --allow-root 2>/dev/null || true
fi

# Mu-plugin balance tags
MU_DIR="$WP/wp-content/mu-plugins"
mkdir -p "$MU_DIR"
if [ ! -f "$MU_DIR/force-layout-balance.php" ]; then
    cat > "$MU_DIR/force-layout-balance.php" << 'MUPHP'
<?php
add_filter("the_content", "force_balance_tags", 99);
add_filter("the_excerpt", "force_balance_tags", 99);
MUPHP
    ok "Mu-plugin force-layout-balance installé."
fi

echo ""
echo -e "${G}══════════════════════════════════════════════════════════════${N}"
echo -e "${G}  Restauration de ${SLUG:-?} terminée !${N}"
echo -e "${G}  Site : $WP${N}"
if [ -n "$URL" ]; then
    echo -e "${G}  URL  : $URL${N}"
fi
echo -e "${G}══════════════════════════════════════════════════════════════${N}"
echo ""
