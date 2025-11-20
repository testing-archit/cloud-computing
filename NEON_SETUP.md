# Neon PostgreSQL Database Setup

This project is now configured to use **Neon** (serverless PostgreSQL) for production deployments.

## Quick Start

### 1. Your Neon Connection Details (Already Configured ✓)
```
Host: ep-quiet-morning-a18t66kf-pooler.ap-southeast-1.aws.neon.tech
User: neondb_owner
Database: neondb
Region: ap-southeast-1 (Singapore)
```

**Connection string format:**
```
postgresql://neondb_owner:PASSWORD@ep-quiet-morning-a18t66kf-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

### 2. Set Environment Variables Locally

Create or update `.env.local` in your project root (DO NOT commit this file):

```bash
cp .env.example .env.local
```

Edit `.env.local` and replace:
```
DATABASE_URL=postgresql://neondb_owner:npg_bi2y7HDWvapA@ep-quiet-morning-a18t66kf-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
SECRET_KEY=your-super-secure-random-key
JWT_SECRET_KEY=your-jwt-super-secure-key
FLASK_ENV=production
```

### 3. Activate Virtualenv & Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run Migrations (If DB Schema Changes)

```bash
# Set environment variable
export DATABASE_URL='postgresql://neondb_owner:npg_PASSWORD@...'
export FLASK_APP=controller.app

# Create a new migration after schema changes
flask db migrate -m "describe your change"

# Apply migrations
flask db upgrade
```

### 5. Start the Flask App

```bash
# Load env vars from .env.local
export $(cat .env.local | xargs)

# Run the app
python -m controller.app
```

App will be available at `http://localhost:8000`

## Production Deployment

### Option A: Docker Compose (with Neon)

Create `docker-compose.override.yml`:
```yaml
version: '3.9'

services:
  controller:
    environment:
      DATABASE_URL: "postgresql://neondb_owner:npg_PASSWORD@ep-quiet-morning-a18t66kf-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
      SECRET_KEY: "YOUR_SECURE_KEY"
      JWT_SECRET_KEY: "YOUR_JWT_KEY"
    depends_on: []  # Remove postgres dependency
```

Run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build
```

### Option B: Cloud Platforms

**Render.com / Railway / Heroku / Fly.io:**

1. Set these environment variables in your platform's dashboard:
   - `DATABASE_URL` → your Neon connection string
   - `SECRET_KEY` → strong random string
   - `JWT_SECRET_KEY` → strong random string
   - `FLASK_ENV` → `production`

2. Deploy your app (via git, Docker image, etc.)

3. Run migrations (one-time):
   ```bash
   flask db upgrade
   ```

## Database Tables

The following tables are automatically created:

- **user** — Student and admin accounts
- **agent** — Compute nodes/agents
- **booking** — Resource bookings
- **alembic_version** — Migration tracking

Check tables:
```bash
psql -h ep-quiet-morning-a18t66kf-pooler.ap-southeast-1.aws.neon.tech -U neondb_owner -d neondb
# password: npg_bi2y7HDWvapA

\dt  # List tables
```

## Security Best Practices

- ✅ Never commit `.env` or real passwords to git
- ✅ Use `.env.local` for local development (added to `.gitignore`)
- ✅ Keep `.env.example` sanitized with dummy values
- ✅ Rotate DB credentials periodically
- ✅ Use Neon's IP allowlisting if available
- ✅ Enable SSL (`sslmode=require` is already set)

## Troubleshooting

**Connection refused?**
- Verify your IP can reach Neon (firewall/VPN)
- Check `sslmode=require` is in the URL
- Confirm credentials at https://console.neon.tech

**Migration fails?**
- Ensure `DATABASE_URL` and `FLASK_APP` are exported
- Run `flask db current` to see applied migrations
- Run `flask db history` to see all migrations

**Tables don't exist?**
- Run `flask db upgrade` to apply any pending migrations
- Or run `python -c "from controller.app import create_app; create_app()"` to auto-create tables

## Further Reading

- [Neon Documentation](https://neon.tech/docs)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
