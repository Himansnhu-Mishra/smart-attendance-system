#!/usr/bin/env bash

# Update and install dependencies for dlib
apt-get update && apt-get install -y cmake libopenblas-dev liblapack-dev libx11-dev

# Continue with normal installation
pip install -r requirements.txt
