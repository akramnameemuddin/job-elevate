#!/usr/bin/env bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Resetting resume templates..."
python manage.py reset_templates

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build completed successfully!"