#!/usr/bin/env bash

pip install -r ../requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py load_default_templates
python manage.py collectstatic --noinput