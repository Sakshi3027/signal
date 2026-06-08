#!/usr/bin/env bash
set -e
pip install --upgrade pip
pip install -r requirements.txt
pip install -e packages/ingestion
pip install -e packages/agent
pip install -e packages/storage
