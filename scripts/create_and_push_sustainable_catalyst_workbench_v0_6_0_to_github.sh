#!/usr/bin/env bash
set -euo pipefail

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-workbench"
ZIP="$HOME/Downloads/sustainable-catalyst-workbench-v0.6.0-repo.zip"
WORKDIR="$HOME/Downloads/sustainable-catalyst-workbench"
REMOTE="git@github.com:${ORG}/${REPO}.git"

echo "Checking local requirements"
command -v git >/dev/null 2>&1 || { echo "git is required"; exit 1; }
command -v unzip >/dev/null 2>&1 || { echo "unzip is required"; exit 1; }
[ -f "$ZIP" ] || { echo "Could not find repo zip: $ZIP"; exit 1; }

echo "Preparing repository folder"
rm -rf "$WORKDIR"
unzip -q "$ZIP" -d "$HOME/Downloads"
cd "$WORKDIR"

echo "Running secret scan"
if grep -RInE '(sk-proj-[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9_\-]{30,}|OPENAI_API_KEY=[A-Za-z0-9_\-]{20,})' . \
  --exclude-dir=.git --exclude='*.zip' --exclude='.env.example' --exclude='create_and_push_*' ; then
  echo "Potential secret found. Aborting."
  exit 1
fi

echo "Initializing git"
rm -rf .git
git init
git add .
git commit -m "Sustainable Catalyst Workbench v0.6.0"
git branch -M main

echo "Preparing GitHub remote"
if command -v gh >/dev/null 2>&1; then
  if ! gh repo view "${ORG}/${REPO}" >/dev/null 2>&1; then
    echo "Creating GitHub repository ${ORG}/${REPO}"
    gh repo create "${ORG}/${REPO}" --private --description "AI-enabled research and analytics workbench for Sustainable Catalyst" --source=. --remote=origin --push
    echo "Created and pushed: https://github.com/${ORG}/${REPO}"
    exit 0
  fi
fi

git remote remove origin >/dev/null 2>&1 || true
git remote add origin "$REMOTE"
git push -u origin main

echo "Pushed to https://github.com/${ORG}/${REPO}"
