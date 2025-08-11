#!/usr/bin/env bash

pip install -r ../requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py create_resume_templates
python manage.py collectstatic --noinput