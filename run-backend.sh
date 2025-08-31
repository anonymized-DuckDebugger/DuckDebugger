#!/bin/bash

echo ">>> RUNNING mockserver.py as backend-only... <<<"
export BACKENDONLY=1
cd barebones_js && ./mockserver.py
