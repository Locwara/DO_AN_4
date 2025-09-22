#!/bin/bash
set -x  # Debug mode
echo "BUILD START"

echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

echo "Creating staticfiles_build directory..."
mkdir -p staticfiles_build/static

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Checking staticfiles_build directory:"
ls -la staticfiles_build/

echo "BUILD END"
