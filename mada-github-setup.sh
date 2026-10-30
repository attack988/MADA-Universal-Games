#!/usr/bin/env bash
# Creates a new public MADA-Anywhere repository and enables Pages using gh.
# Does not modify or delete the MADA Universal Games repository.
set -Eeuo pipefail
OWNER=attack988
REPO=MADA-Anywhere
BASE="${MADA_BASE:-$HOME/MADA-Apps}"
GAMES="$BASE/MADA-Universal-Games"
DEST="$BASE/MADA-Anywhere-GitHub"
has(){ command -v "$1" >/dev/null 2>&1; }
for c in gh git unzip python3; do has "$c" || { echo "Missing $c. Install: sudo apt install -y gh git unzip python3"; exit 1; }; done
if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub login required; follow the prompts:"
  gh auth login -h github.com -p https -w
fi
LOGIN="$(gh api user --jq .login)"
[[ "$LOGIN" == "$OWNER" ]] || { echo "Authenticated as $LOGIN, expected $OWNER. Please switch GitHub account."; exit 1; }
if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  echo "The separate repository already exists: https://github.com/$OWNER/$REPO"
else
  [[ -f "$GAMES/apps/MADA-Anywhere/MADA_Anywhere_v2.zip" ]] || { echo "First run: mada setup"; exit 1; }
  [[ ! -e "$DEST" ]] || { echo "$DEST already exists. Not overwriting it."; exit 1; }
  mkdir -p "$DEST"
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  unzip -q "$GAMES/apps/MADA-Anywhere/MADA_Anywhere_v2.zip" -d "$TMP"
  cp -a "$TMP/MADA_Anywhere/." "$DEST/"
  cp "$GAMES/apps/MADA-Anywhere/README.md" "$DEST/README.md"
  cp "$GAMES/apps/MADA-Anywhere/MADA_Anywhere_v2.zip" "$DEST/MADA_Anywhere_v2.zip"
  mkdir -p "$DEST/docs" "$DEST/.github/workflows"
  cp "$GAMES/docs/anywhere/index.html" "$DEST/docs/index.html"
  cp "$GAMES/docs/anywhere/preview.svg" "$DEST/docs/preview.svg"
  cp "$GAMES/docs/site.css" "$DEST/docs/site.css"
  : > "$DEST/docs/.nojekyll"
  python3 - "$DEST" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
readme=p/'README.md'
s=readme.read_text(encoding='utf8')
s=s.replace('../../docs/anywhere/preview.svg','docs/preview.svg')
s=s.replace('../../docs/anywhere/index.html','docs/index.html')
s=s.replace('https://github.com/attack988/MADA-Universal-Games/tree/main/apps/MADA-Anywhere','https://github.com/attack988/MADA-Anywhere')
readme.write_text(s,encoding='utf8')
page=p/'docs/index.html'
s=page.read_text(encoding='utf8').replace('href="../site.css"','href="./site.css"')
s=s.replace('https://github.com/attack988/MADA-Universal-Games/tree/main/apps/MADA-Anywhere','https://github.com/attack988/MADA-Anywhere')
s=s.replace('https://raw.githubusercontent.com/attack988/MADA-Universal-Games/main/apps/MADA-Anywhere/MADA_Anywhere_v2.zip','https://raw.githubusercontent.com/attack988/MADA-Anywhere/main/MADA_Anywhere_v2.zip')
page.write_text(s,encoding='utf8')
PY
  cat > "$DEST/.github/workflows/pages.yml" <<'YAML'
name: Publish MADA Anywhere Website
on:
  push:
    branches: [main]
    paths: ['docs/**', '.github/workflows/pages.yml']
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: github-pages
  cancel-in-progress: false
jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v4
        with:
          path: ./docs
      - id: deployment
        uses: actions/deploy-pages@v4
YAML
  git -C "$DEST" init -b main
  git -C "$DEST" add .
  USER_ID="$(gh api user --jq .id)"
  git -C "$DEST" -c "user.name=$LOGIN" -c "user.email=$USER_ID+$LOGIN@users.noreply.github.com" commit -m "Initial MADA Anywhere release and bilingual website"
  gh auth setup-git
  gh repo create "$OWNER/$REPO" --public --description "MADA Anywhere — media downloader with bilingual website and cross-platform PWA" --source="$DEST" --remote=origin --push
  echo "Published new repository: https://github.com/$OWNER/$REPO"
fi
if gh api "repos/$OWNER/$REPO/pages" >/dev/null 2>&1; then
  gh api -X PUT "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null || echo "Could not select workflow build type automatically."
else
  gh api -X POST "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null || echo "Pages could not be enabled automatically. Check repository Settings > Pages."
fi
gh workflow run pages.yml -R "$OWNER/$REPO" --ref main || echo "Please run the Pages workflow manually if it did not start."
echo "Repository: https://github.com/$OWNER/$REPO"
echo "Expected site after deployment: https://$OWNER.github.io/$REPO/"
echo "Check build: https://github.com/$OWNER/$REPO/actions"
