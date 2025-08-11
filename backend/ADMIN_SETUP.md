# Admin Setup for JobElevate - Render Deployment

## 🔧 Environment Variables for Render

Add these environment variables in your Render dashboard:

```
ADMIN_USERNAME=admin
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=YourSecurePassword123!
```

## 🚀 Deployment Process

1. **Push your code to GitHub** (make sure build.sh includes `python manage.py create_admin`)

2. **In Render Dashboard:**
   - Go to your web service
   - Add the environment variables above
   - Redeploy the service

3. **Admin Access:**
   - URL: `https://your-app-name.onrender.com/admin/`
   - Username: `admin` (or your custom username)
   - Password: Your secure password

## 🔐 Default Credentials (if no env vars set)

- **Username:** `admin`
- **Email:** `admin@jobelevate.com`
- **Password:** `JobElevate2025!`

## 📊 What You Can Access in Admin Panel

### User Management
- View all registered users (students, professionals, recruiters)
- User profiles, skills, experience
- Email verification status

### Job Management
- All job listings posted by recruiters
- Job applications and their status
- Job views and bookmarks analytics

### Recruiter Management
- Recruiter profiles and companies
- Messages between users and recruiters

### Analytics Data
- User job preferences
- Job recommendations and scores
- User similarity calculations
- Job views and engagement metrics

### System Administration
- User permissions and groups
- Site-wide settings
- Data exports and reports

## 🛠️ Manual Admin Creation (Alternative)

If automatic creation fails, use Render Shell:

1. Go to Render Dashboard > Your Service > Shell
2. Click "Launch Shell"
3. Run: `python manage.py create_admin`

Or create interactively:
```bash
python manage.py createsuperuser
```

## 🔒 Security Best Practices

1. **Change default credentials** in production
2. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. **Set custom admin URL** (optional):
   ```python
   # In settings.py
   ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')
   ```
4. **Limit admin access** to trusted IPs if needed
5. **Enable 2FA** for admin accounts (future enhancement)

## 📱 Admin Features Available

- **Dashboard:** Overview of users, jobs, applications
- **User Analytics:** Registration trends, user types distribution
- **Job Analytics:** Most viewed jobs, application rates
- **Content Management:** Moderate job postings, user reports
- **System Health:** Database status, error logs
- **Export Tools:** CSV/Excel exports for reports

## 🎯 Admin User Capabilities

The admin user has full access to:
- ✅ View/Edit all user accounts
- ✅ Manage job postings and applications
- ✅ Access analytics and reports
- ✅ Configure system settings
- ✅ Monitor user activity
- ✅ Export data for analysis
- ✅ Manage recruiter accounts
- ✅ Handle user support requests

## 🚨 Troubleshooting

**Admin creation fails:**
- Check environment variables are set correctly
- Verify database connection
- Check logs in Render dashboard

**Can't access admin panel:**
- Verify URL: `/admin/` (with trailing slash)
- Check if admin user exists: `python manage.py shell` then `User.objects.filter(is_superuser=True)`
- Verify credentials

**Forgot admin password:**
- Use Render Shell: `python manage.py changepassword admin`
- Or create new admin: `python manage.py create_admin --username newadmin`
