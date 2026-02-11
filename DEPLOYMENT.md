# Job Elevate — Docker Deployment Guide (AWS EC2)

This guide covers deploying Job Elevate on an AWS EC2 instance using Docker.

---

## Architecture

```
Internet → Nginx (port 80/443) → Gunicorn (port 8000) → Django App
                                                            ↓
                                                     PostgreSQL (port 5432)
```

**Containers:**
| Container | Purpose |
|-----------|---------|
| `jobelevate-web` | Django + Gunicorn (app server) |
| `jobelevate-db` | PostgreSQL 16 (database) |
| `jobelevate-nginx` | Nginx (reverse proxy, SSL, static files) |
| `jobelevate-certbot` | Let's Encrypt auto-renewal |

---

## Step 1: Prepare Your AWS EC2 Instance

### Launch EC2
- **AMI:** Ubuntu 22.04 LTS
- **Instance type:** t2.small (minimum) or t2.medium (recommended)
- **Storage:** 20 GB minimum
- **Security Group inbound rules:**

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP |
| 443 | TCP | 0.0.0.0/0 | HTTPS |

### SSH into your instance
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Install Docker & Docker Compose
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Log out and back in for group change to take effect
exit
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# Verify
docker --version
docker compose version
```

---

## Step 2: Deploy the Application

### Clone your repository
```bash
git clone https://github.com/your-username/job-elevate.git
cd job-elevate
```

### Create the environment file
```bash
cp .env.docker.example .env.docker
nano .env.docker
```

**Fill in ALL values:**
```env
SECRET_KEY=generate-a-50-char-random-string-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-ec2-public-ip

DATABASE_URL=postgres://jobelevate:YOUR_STRONG_DB_PASSWORD@db:5432/jobelevate
DB_PASSWORD=YOUR_STRONG_DB_PASSWORD

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

GOOGLE_API_KEY=your-gemini-api-key

CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

> **Generate a secret key:**
> ```bash
> python3 -c "import secrets; print(secrets.token_urlsafe(50))"
> ```

### Update Nginx config with your domain
```bash
nano docker/nginx.conf
# Replace "your-domain.com" with your actual domain everywhere
```

### Build and start all containers
```bash
docker compose up -d --build
```

This will:
1. Build the Django app image
2. Start PostgreSQL and wait for it to be healthy
3. Run migrations automatically
4. Collect static files
5. Start Gunicorn (3 workers)
6. Start Nginx on ports 80/443

### Verify everything is running
```bash
docker compose ps
docker compose logs web    # Check app logs
docker compose logs db     # Check database logs
docker compose logs nginx  # Check nginx logs
```

---

## Step 3: Initialize Data

### Create superuser
```bash
docker compose exec web python backend/manage.py createsuperuser
```

### Seed assessment questions
```bash
docker compose exec web python backend/manage.py add_questions
```

### Seed demo data & train ML model
```bash
docker compose exec web python backend/manage.py seed_demo_data
docker compose exec web python backend/manage.py train_fit_model --synthetic 2000
docker compose exec web python backend/manage.py evaluate_model
```

---

## Step 4: Set Up Your Domain (DNS)

In your domain registrar (e.g., GoDaddy, Namecheap, Route53):

| Type | Name | Value |
|------|------|-------|
| A | @ | your-ec2-public-ip |
| A | www | your-ec2-public-ip |

Wait 5-10 minutes for DNS propagation. Test:
```bash
ping your-domain.com
```

---

## Step 5: Enable HTTPS (SSL)

### Get SSL certificate from Let's Encrypt
```bash
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d your-domain.com \
    -d www.your-domain.com \
    --email your-email@gmail.com \
    --agree-tos \
    --no-eff-email
```

### Enable HTTPS in Nginx
```bash
nano docker/nginx.conf
```

1. **Uncomment** the `return 301 https://...` line in the HTTP server block
2. **Comment out** the HTTP proxy/static location blocks (lines 26-45)
3. **Uncomment** the entire HTTPS server block at the bottom
4. Replace `your-domain.com` with your actual domain

### Restart Nginx
```bash
docker compose restart nginx
```

Your site is now live at `https://your-domain.com`

---

## Common Commands

```bash
# View logs (live)
docker compose logs -f web

# Restart a specific container
docker compose restart web

# Stop everything
docker compose down

# Stop and remove all data (DESTRUCTIVE)
docker compose down -v

# Rebuild after code changes
git pull
docker compose up -d --build

# Access Django shell
docker compose exec web python backend/manage.py shell

# Database backup
docker compose exec db pg_dump -U jobelevate jobelevate > backup_$(date +%Y%m%d).sql

# Database restore
docker compose exec -T db psql -U jobelevate jobelevate < backup_20260211.sql

# Retrain ML model
docker compose exec web python backend/manage.py train_fit_model --synthetic 2000
```

---

## Updating the Application

When you push new code:
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
cd job-elevate
git pull origin main
docker compose up -d --build
```

The entrypoint script automatically runs migrations and collects static files on every restart.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `502 Bad Gateway` | `docker compose logs web` — check if Gunicorn started |
| `Static files 404` | `docker compose exec web python backend/manage.py collectstatic --noinput` |
| Database connection refused | `docker compose ps db` — ensure DB is healthy |
| Permission denied on media/ | `docker compose exec web chmod -R 755 backend/media/` |
| SSL cert expired | `docker compose run --rm certbot renew && docker compose restart nginx` |
| Out of disk space | `docker system prune -a` to clean old images |

---

## Cost Estimate (AWS)

| Resource | Monthly Cost |
|----------|-------------|
| t2.small EC2 | ~$17 |
| 20 GB EBS | ~$2 |
| Elastic IP | Free (if attached) |
| **Total** | **~$19/month** |

Free tier: t2.micro is free for 12 months but may be tight on RAM for this stack.
