#!/usr/bin/env bash
set -e  # Exit on any error

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Checking Django installation..."
python -c "import django; print('Django version:', django.get_version())"

echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Resetting resume templates..."
python manage.py reset_templates

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build completed successfully!"