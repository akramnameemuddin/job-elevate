#!/usr/bin/env bash

echo "Activating virtual environment..."
source ../venv/Scripts/activate

echo "Running migrations and collecting static files..."
cd backend || exit

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
