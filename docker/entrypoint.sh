#!/bin/bash
set -e

cd /app/backend

echo "==> Running migrations …"
python manage.py migrate --noinput

echo "==> Collecting static files …"
python manage.py collectstatic --noinput

# ── Seed data (idempotent — only creates if not already present) ──
echo "==> Seeding assessment data (skills + questions) …"
python manage.py populate_assessment_data

echo "==> Seeding courses …"
python manage.py populate_courses

echo "==> Seeding community (tags + events) …"
python manage.py seed_community

echo "==> Creating resume templates …"
python manage.py create_resume_templates

echo "==> Creating admin user …"
python manage.py create_admin

echo "==> Seeding demo data (users + jobs + applications) …"
python manage.py seed_demo_data

echo "==> Training ML model …"
python manage.py train_fit_model --synthetic 2000 || echo "WARNING: ML training failed (non-critical)"

echo "==> Starting server …"
exec "$@"
