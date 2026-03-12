# The Hub

A lightweight Django content platform for creators — publish blog posts and courses, accept payments via Paystack or Flutterwave, and manage everything from Django's admin.

Built with Python 3.11, Django 5.2, CKEditor 5, HTMX, and Tailwind CSS.

---

## Features

- **Unified content feed** — posts and courses in a single infinite-scroll list
- **Category management** — create and manage categories from the admin
- **Rich text editor** — CKEditor 5 with image upload, YouTube embeds, and code blocks
- **WebP thumbnail conversion** — all uploaded images are auto-converted to WebP
- **Paid courses** — gate external resource URLs behind Paystack or Flutterwave payments
- **User accounts** — register, login, profile edit, password change via django-allauth
- **Purchased content dashboard** — users can see all their enrolled courses in one place
- **Site settings** — manage site name, social handles, and contact email from the admin
- **Dynamic meta tags** — full Open Graph and Twitter Card support on every page
- **Mobile responsive** — compact card grid, horizontal category strip, sticky header

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | Django 5.2 |
| Rich text | CKEditor 5 (`django-ckeditor-5`) |
| Auth | django-allauth |
| Frontend | Tailwind CSS, HTMX |
| Payments | Paystack, Flutterwave |
| Image processing | Pillow |
| Static files | WhiteNoise + Brotli |
| Database | SQLite (dev) / PostgreSQL (prod) |

---

## Project structure

```
hub/
├── config/                  # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── content/                 # Main app
│   ├── admin.py
│   ├── context_processors.py
│   ├── models.py            # Category, Post, Course, Enrollment, SiteSettings
│   ├── payments.py          # Paystack + Flutterwave logic
│   ├── templatetags/
│   │   └── content_tags.py  # youtube_embed filter
│   ├── urls.py
│   ├── utils.py             # WebP conversion
│   └── views.py
├── templates/
│   ├── base.html
│   ├── account/             # allauth templates
│   │   ├── login.html
│   │   ├── signup.html
│   │   └── password_change.html
│   └── content/
│       ├── list.html
│       ├── post_detail.html
│       ├── course_detail.html
│       ├── payment_select.html
│       ├── profile.html
│       └── partials/
│           └── cards.html   # HTMX infinite scroll partial
├── static/
│   ├── css/
│   │   ├── tailwind.css
│   │   └── ckeditor5.css
│   └── js/
│       └── htmx.js
├── media/                   # Uploaded files (gitignored)
├── .env                     # Secret config (gitignored)
├── .env.example             # Safe template to commit
├── .gitignore
├── manage.py
└── requirements.txt
```

---

## Local setup

### 1. Clone and create environment

```bash
git clone https://github.com/yourname/hub.git
cd hub
python3.11 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

```
SECRET_KEY=<generate one at https://djecrety.ir>
DEBUG=True
```

### 3. Run migrations and create superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Start the dev server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` for the site and `http://127.0.0.1:8000/admin` for the admin.

---

## Admin quickstart

After logging into the admin:

1. **Site Settings** — set your site name, social handles, and contact email
2. **Categories** — create at least one category before adding content
3. **Posts** — write blog posts with the rich text editor
4. **Courses** — same as posts, with optional video URL, external resource, and payment gating

To make a course paid: tick **Is paid**, enter a **Price** in NGN, and fill in the **External resource URL**. The resource URL will be hidden behind payment until a user completes checkout.

---

## Email configuration

The platform uses Django's email system for allauth (password reset, email confirmation).

### Gmail (recommended for small deployments)

1. Enable 2-Step Verification on your Google account
2. Go to **Google Account → Security → App Passwords**
3. Generate a password for "Mail" and copy it
4. Add to `.env`:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx
DEFAULT_FROM_EMAIL=The Hub <you@gmail.com>
```

### Other providers

| Provider | HOST | PORT |
|---|---|---|
| Outlook / Hotmail | `smtp.office365.com` | `587` |
| Zoho Mail | `smtp.zoho.com` | `587` |
| SendGrid | `smtp.sendgrid.net` | `587` |
| Mailgun | `smtp.mailgun.org` | `587` |

For SendGrid and Mailgun, `EMAIL_HOST_USER` is `apikey` or `postmaster@yourdomain`, and `EMAIL_HOST_PASSWORD` is your API key.

### Enable email verification

Once SMTP is configured, switch in `settings.py`:

```python
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
```

---

## Payment setup

### Paystack

1. Create an account at [paystack.com](https://paystack.com)
2. Go to **Settings → API Keys & Webhooks**
3. Copy your test keys into `.env`
4. Set your webhook URL to `https://yourdomain.com/payment/verify/paystack/<reference>/`

### Flutterwave

1. Create an account at [flutterwave.com](https://flutterwave.com)
2. Go to **Settings → API** and copy your test keys into `.env`
3. Set your redirect URL — the app handles this automatically via the `callback_url` parameter

Switch to live keys in `.env` when you're ready to go live — no code changes needed.

---

## Deployment checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Set `ALLOWED_HOSTS=yourdomain.com` in `.env`
- [ ] Generate a strong `SECRET_KEY`
- [ ] Switch to PostgreSQL (see below)
- [ ] Run `python manage.py collectstatic`
- [ ] Configure SMTP and set `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'`
- [ ] Replace Paystack/Flutterwave test keys with live keys
- [ ] Set up HTTPS (required by both payment providers)
- [ ] Configure a process manager (gunicorn + systemd or supervisor)
- [ ] Point a reverse proxy (nginx) to gunicorn

### PostgreSQL setup

```bash
pip install psycopg2-binary
```

Add to `.env`:
```env
DATABASE_URL=postgres://user:password@localhost:5432/hub_db
```

In `settings.py`:
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}
```

```bash
pip install dj-database-url
```

### Gunicorn

```bash
pip install gunicorn
gunicorn config.wsgi:application --workers 3 --bind 0.0.0.0:8000
```

### Nginx config (minimal)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/hub/staticfiles/;
    }

    location /media/ {
        alias /path/to/hub/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Generating a SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Requirements

```
django==5.2
django-ckeditor-5
django-allauth
pillow
python-dotenv
whitenoise[brotli]
```

For production, also add:
```
gunicorn
psycopg2-binary
dj-database-url
django-redis        # optional, for Redis cache
```

---

## License

MIT — free to use, modify, and deploy.