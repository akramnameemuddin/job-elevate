# JobElevate — Deployment Guide (AWS EC2)

Deploys Django + Gunicorn + Nginx directly on an EC2 instance.
No Docker required.

---

## Architecture

```
Internet → Nginx (port 80/443, SSL) → Gunicorn (127.0.0.1:8000) → Django
                                                                       ↓
                                                              AWS RDS PostgreSQL
                                                              AWS S3 (static/media)
```

---

## Prerequisites

| Resource | Spec |
|---|---|
| EC2 | Ubuntu 24.04 LTS, t2.small or larger |
| Storage | 20 GB EBS minimum |
| RDS | PostgreSQL 16 in same VPC as EC2 |
| S3 | Bucket for static + media files |
| Domain | A record pointing to EC2 Elastic IP |

### Security Group inbound rules

| Port | Source | Purpose |
|---|---|---|
| 22 | Your IP | SSH |
| 80 | 0.0.0.0/0 | HTTP |
| 443 | 0.0.0.0/0 | HTTPS |

---

## Step 1 — Server Setup

```bash
# Connect
ssh -i your-key.pem ubuntu@YOUR-EC2-IP

# System packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip nginx certbot python3-certbot-nginx git

# Add swap — prevents OOM on t2.micro/t2.small during startup
sudo fallocate -l 1.2G /swapfile
sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Clone the repo
git clone https://github.com/akramnameemuddin/job-elevate.git
cd job-elevate

# Create venv at project root (NOT inside backend/)
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Step 2 — Environment Variables

```bash
cp deploy/env.production.example backend/backend/.env
nano backend/backend/.env
```

Fill in every value:

```env
SECRET_KEY=your-50-char-random-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,YOUR-EC2-IP

# AWS RDS PostgreSQL
DATABASE_URL=postgres://jobelevate:StrongPass@your-rds-endpoint.rds.amazonaws.com:5432/jobelevate

# Email (Gmail App Password)
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# Google Gemini
GOOGLE_API_KEY=your-gemini-api-key

# AWS S3
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Security
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

Generate a secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(50))"
```

---

## Step 3 — Database & Static Files

```bash
cd ~/job-elevate/backend

python manage.py migrate
python manage.py collectstatic --noinput    # uploads to S3
```

---

## Step 4 — Seed Data (run once)

```bash
python manage.py populate_assessment_data   # skill categories + skills
python manage.py create_resume_templates    # 3 resume templates
python manage.py populate_courses           # learning course catalog
python manage.py seed_community             # community tags + sample posts
python manage.py seed_demo_data             # demo users, jobs, applications
python manage.py createsuperuser            # or: python manage.py create_admin
```

All commands are idempotent — safe to re-run.

---

## Step 5 — Gunicorn Systemd Service

```bash
sudo cp ~/job-elevate/deploy/gunicorn.service /etc/systemd/system/gunicorn.service
```

> **t2.micro tip:** Edit the service file and change `--workers 3` to `--workers 1`.
> Each worker uses ~180 MB RAM. 3 workers can OOM-kill on a 1 GB instance.

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn    # should show "active (running)"
```

---

## Step 6 — Nginx

```bash
sudo cp ~/job-elevate/deploy/nginx-jobelevate.conf /etc/nginx/sites-available/jobelevate
```

Edit the file and replace `jobelevates.akramnaeemuddin.me` with your domain:
```bash
sudo nano /etc/nginx/sites-available/jobelevate
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/jobelevate /etc/nginx/sites-enabled/
sudo nginx -t          # must print "syntax is ok"
sudo systemctl reload nginx
```

---

## Step 7 — SSL Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com \
    --email your-email@gmail.com --agree-tos --no-eff-email
sudo systemctl reload nginx
```

Certbot auto-renews every 90 days via a systemd timer. Verify:
```bash
sudo certbot renew --dry-run
```

Your site is now live at `https://yourdomain.com`

---

## Updating After a Code Push

```bash
ssh -i your-key.pem ubuntu@YOUR-EC2-IP
cd ~/job-elevate
git fetch origin && git reset --hard origin/master
source venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## Operations Reference

```bash
# Service status
sudo systemctl status gunicorn
sudo systemctl status nginx

# Live logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log
tail -f ~/job-elevate/logs/django.log

# Restart services
sudo systemctl restart gunicorn
sudo systemctl reload nginx

# Django shell
cd ~/job-elevate/backend && source ../venv/bin/activate
python manage.py shell

# Run tests
python manage.py test --verbosity=2

# Resources (t2.micro: keep RAM < 900 MB)
free -h
df -h
```

---

## AWS S3 Bucket Policy (Public Read for Static Files)

In AWS Console → S3 → your bucket → **Permissions** → **Bucket policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
  }]
}
```

Also ensure:
- **Block Public Access** → Off
- **Object Ownership** → "Bucket owner enforced" (ACLs disabled)

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `502 Bad Gateway` | `sudo journalctl -u gunicorn -n 50` — check for import errors |
| Static files 404 | `python manage.py collectstatic --noinput` + check `USE_S3=True` |
| DB connection refused | Check RDS security group allows port 5432 from EC2 security group |
| OOM / gunicorn killed | Reduce to `--workers 1` in gunicorn.service + ensure 1.2 GB swap exists |
| SSH timeout in CI/CD | EC2 Security Group → add SSH inbound rule `0.0.0.0/0 port 22` |
| SSL cert expired | `sudo certbot renew && sudo systemctl reload nginx` |
| Gemini questions not generating | Check `GOOGLE_API_KEY` in `.env`; run `python manage.py check_api_status` |

---

## Cost Estimate (AWS us-east-1)

| Resource | Monthly Cost |
|---|---|
| t2.micro EC2 (Free tier 12 months) | $0 → ~$8 |
| t2.small EC2 | ~$17 |
| 20 GB EBS gp3 | ~$1.60 |
| RDS db.t3.micro PostgreSQL | ~$15 |
| S3 + data transfer (light usage) | ~$1 |
| Elastic IP (attached) | Free |
| **Total (t2.micro + RDS)** | **~$18/month** |
