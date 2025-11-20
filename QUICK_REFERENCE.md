# Quick Reference Card

## 🚀 One-Liner Deployment

```bash
cd /Users/archit/Desktop/cloud-project/compute-booking && cp .env.example .env && docker-compose up --build
```

## 📍 Access Points

| Service | URL | Port |
|---------|-----|------|
| Frontend | http://localhost:3000 | 3000 |
| API | http://localhost:8000/api | 8000 |
| Traefik | http://localhost:8080 | 8080 |
| Agent 1 | http://localhost:5001 | 5001 |
| Agent 2 | http://localhost:5002 | 5002 |
| DB | localhost:5432 | 5432 |
| Redis | localhost:6379 | 6379 |

## 📝 Default Login Credentials

**Admin:**
- Email: `admin@test.com`
- Password: `admin123456`

**Student:**
- Email: `student@test.com`
- Password: `student123456`

(Create test users via `/api/auth/register`)

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f controller

# Run tests
docker-compose exec controller pytest tests/ -v

# Run tests with coverage
docker-compose exec controller pytest tests/ --cov=controller

# SSH into container
docker-compose exec controller bash

# Check service health
curl http://localhost:8000/api/auth/login
curl http://localhost:5001/health

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Remove volumes (CAREFUL!)
docker-compose down -v
```

## 📊 Database

```bash
# Connect to database
psql -U compute_user -d compute_booking -h localhost

# List tables
\dt

# View users
SELECT id, name, email, role FROM "user";

# View agents
SELECT id, name, ip, status, available_cpu, available_mem FROM agent;

# View bookings
SELECT id, user_id, agent_id, status, start_time, end_time FROM booking;
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/conftest.py::TestAuth -v

# Run with coverage
pytest tests/ --cov=controller --cov-report=html

# Run with specific marker
pytest tests/ -m "not integration"
```

## 🐛 Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| Containers won't start | `docker-compose logs` to check errors |
| Port 8000 already in use | `lsof -i :8000` then `kill <PID>` |
| Database connection failed | Wait 30s, DB takes time to start |
| Agent health check fails | Ensure Docker daemon running on node |
| Frontend blank page | Check browser console, API URL correct? |
| Tests failing | Ensure postgres service running |

## 📋 Folder Structure

```
compute-booking/
├── controller/              # Flask backend
│   ├── routes/             # API endpoints
│   ├── utils/              # Scheduler, WoL
│   ├── models.py           # Database models
│   └── schemas.py          # Input validation
├── agent/                  # Agent Flask app
├── frontend/               # React UI
│   └── src/components/     # React components
├── tests/                  # Pytest suite
├── docker-compose.yml      # Complete stack
├── README.md               # Full documentation
├── NODE_SETUP.md           # Worker node guide
└── deploy.sh               # Deploy script
```

## 🔑 API Quick Reference

### Register/Login
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@test.com",
    "password": "securepass123",
    "role": "student"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@test.com",
    "password": "securepass123"
  }'
```

### Create Booking
```bash
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:8000/api/student/book \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cpu": 2,
    "memory": "4g",
    "image": "jupyter/notebook",
    "start_time": "2025-11-14T10:00:00",
    "duration_hr": 2
  }'
```

### Approve Booking (Admin)
```bash
ADMIN_TOKEN="admin_jwt_token"
BOOKING_ID=1
AGENT_ID=1

curl -X POST http://localhost:8000/api/admin/approve/$BOOKING_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": '$AGENT_ID'}'
```

## 🌐 Environment Variables

```bash
# Essential
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://user:pass@host/db

# Optional
PORT=8000
DEBUG=False
AGENT_HOST=0.0.0.0
AGENT_PORT=5000
```

## 📦 Dependencies

**Backend:**
- Flask, Flask-SQLAlchemy, Flask-JWT-Extended
- APScheduler, Requests, Docker SDK
- Marshmallow (validation), psutil (monitoring)

**Frontend:**
- React 18, Vite, Tailwind CSS, Axios

**Infrastructure:**
- Docker, Docker Compose
- PostgreSQL 16, Redis 7
- Traefik 2.11

**Testing:**
- pytest, pytest-flask, pytest-cov

## 🎯 Common Workflows

### 1. Add New Route
1. Create route in `controller/routes/`
2. Add schema in `schemas.py`
3. Add admin/student decorator if needed
4. Write tests in `tests/conftest.py`
5. Update README

### 2. Deploy to Production
1. Edit `.env` with production secrets
2. Run `./deploy.sh`
3. Configure DNS
4. Set up SSL with Traefik

### 3. Add Worker Node
1. Follow `NODE_SETUP.md`
2. Register in database (see NODE_SETUP.md)
3. Verify health: `curl node_ip:5000/health`

### 4. Debug Issue
```bash
# Check logs
docker-compose logs service_name -f

# SSH into container
docker-compose exec service_name bash

# Run tests
docker-compose exec controller pytest tests/ -v
```

## ✨ Performance Tips

- Redis for caching (configured but not used yet)
- Database connection pooling (built-in)
- Async health checks (in scheduler)
- Resource limits per container (configured)
- Smart agent selection (least loaded first)

## 🔐 Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Change JWT_SECRET_KEY in production
- [ ] Use strong PostgreSQL password
- [ ] Enable HTTPS/TLS (Traefik ready)
- [ ] Configure CORS properly
- [ ] Set DEBUG=False in production
- [ ] Use environment secrets, not hardcoded
- [ ] Regularly update dependencies

---

**Last Updated:** November 13, 2025
**Status:** ✅ Production Ready
