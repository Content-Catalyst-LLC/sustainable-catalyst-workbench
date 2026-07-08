#!/usr/bin/env bash
set -euo pipefail

REPO_ZIP="$HOME/Downloads/sustainable-catalyst-workbench-v0.1.0-repo.zip"
WORKDIR="$HOME/Downloads/sustainable-catalyst-workbench-repo"
GITHUB_SSH="git@github.com:Content-Catalyst-LLC/sustainable-catalyst-workbench.git"

printf '\nChecking local requirements\n'
command -v git >/dev/null || { echo "git is required"; exit 1; }
command -v unzip >/dev/null || { echo "unzip is required"; exit 1; }

if [[ ! -f "$REPO_ZIP" ]]; then
  echo "Could not find repo zip: $REPO_ZIP"
  echo "Download sustainable-catalyst-workbench-v0.1.0-repo.zip into your Downloads folder, then run this script again."
  exit 1
fi

rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
unzip -q "$REPO_ZIP" -d "$WORKDIR"

cd "$WORKDIR/sustainable-catalyst-workbench"

printf '\nRunning secret scan\n'
if grep -RInE '(sk-[A-Za-z0-9]|OPENAI_API_KEY=[A-Za-z0-9]|api[_-]?key\s*=\s*["'"'][A-Za-z0-9_-]{20,})' . --exclude-dir=.git; then
  echo "Potential secret found. Aborting."
  exit 1
fi

if [[ ! -d .git ]]; then
  git init
  git branch -M main
fi

git add .
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "Initial Sustainable Catalyst Workbench v0.1.0"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$GITHUB_SSH"
else
  git remote add origin "$GITHUB_SSH"
fi

git push -u origin main

printf '\nDone. Pushed Sustainable Catalyst Workbench v0.1.0 to GitHub.\n'
