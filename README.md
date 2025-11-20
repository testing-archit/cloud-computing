# Compute Booking System

A production-ready compute resource booking platform with role-based access, resource scheduling, Wake-on-LAN integration, and Docker container orchestration.

## Features

✅ **User Authentication** — JWT-based auth with admin/student roles  
✅ **Booking Management** — Create, approve, reject, extend, and cancel bookings  
✅ **Resource Allocation** — CPU and memory limits on containers  
✅ **Agent Management** — Health checks, load balancing, auto-assignment  
✅ **Wake-on-LAN** — Automated machine wake-up before sessions  
✅ **Scheduler** — APScheduler for automated container lifecycle  
✅ **Frontend** — React-based UI for students and admins  
✅ **Docker Integration** — Full containerization with Traefik routing  
✅ **Database** — SQLAlchemy ORM with PostgreSQL support  

## Architecture

```
┌─────────────────┐
│   React UI      │
│  (Frontend)     │
└────────┬────────┘
         │ HTTP/JWT
┌────────▼─────────────┐
│  Flask Controller    │
│  ├── Routes          │
│  ├── Models (SQLa)   │
│  ├── Scheduler       │
│  └── WoL Logic       │
└────┬────────┬────────┘
     │        │
  DB │        │ HTTP
     │        │
┌────▼─┐   ┌──▼──────┐
│ DB   │   │ Agents  │
│ (PG) │   │ (Flask) │
└──────┘   └─┬───┬───┘
            │   │
          ┌─▼─┐ ┌─▼─┐
          │PC1│ │PC2│
          └───┘ └───┘
       (Docker)
```

## Quick Start

### Local Development

1. Clone the repo:
```bash
cd /Users/archit/Desktop/cloud-project/compute-booking
```

2. Create and activate venv:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run controller:
```bash
python -m controller.app
```

Controller will start on `http://localhost:8000`

### Using Docker Compose

1. Copy env file and customize:
```bash
cp .env.example .env
```

2. Build and run:
```bash
docker compose up --build
```

 
### Authentication
```
POST   /api/auth/register       ← Register user
POST   /api/auth/login          ← Login (returns JWT)
POST   /api/auth/logout         ← Logout
```

### Student
```
POST   /api/student/book        ← Create booking
GET    /api/student/bookings    ← View my bookings
POST   /api/student/bookings/:id/cancel
GET    /api/student/profile
```

### Admin
```
GET    /api/admin/bookings?status=pending
POST   /api/admin/approve/:id          ← Approve with optional agent_id
POST   /api/admin/reject/:id           ← Reject with reason
POST   /api/admin/extend/:id           ← Extend session by hours
GET    /api/admin/agents               ← List agents
POST   /api/admin/agents/:id/status    ← Set agent status
GET    /api/admin/stats                ← Dashboard stats
```

## Database Models

### User
```python
id, name, email, password_hash, role (admin/student), 
department, created_at, active
```

### Agent
```python
id, name, ip, mac, port, wol_enabled, status (online/offline/maintenance),
last_seen, total_cpu, available_cpu, total_mem, available_mem, tags
```

### Booking
```python
id, user_id, agent_id, cpu, memory, image, 
start_time, end_time, status, container_name, access_url,
created_at, updated_at, notes, rejection_reason
```

## Configuration

### Environment Variables
```bash
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://user:pass@host/db
PORT=8000
DEBUG=False
AGENT_HOST=0.0.0.0
AGENT_PORT=5000
```

## Deployment

### Production Checklist

- [ ] Use strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Set DATABASE_URL to PostgreSQL (not SQLite)
- [ ] Enable HTTPS with Let's Encrypt (Traefik)
- [ ] Configure DNS and domain names
- [ ] Set up agent machines with systemd service
- [ ] Enable WoL in BIOS on agent machines
- [ ] Test health checks and failover
- [ ] Set up monitoring and logging (e.g., ELK stack)
- [ ] Backup database regularly

### Node Setup (Agent Machine)

1. **Install dependencies:**
```bash
sudo apt update
sudo apt install docker.io python3 python3-pip -y
sudo usermod -aG docker $USER
pip install flask docker requests psutil
```

2. **Create Docker network (shared with Traefik):**
```bash
sudo docker network create proxy
```

3. **Create systemd service** (`/etc/systemd/system/agent.service`):
```ini
[Unit]
Description=Compute Booking Agent
After=docker.service network.target

[Service]
ExecStart=/usr/bin/python3 /opt/agent/agent.py
Restart=always
Environment="AGENT_HOST=192.168.0.105"
Environment="AGENT_PORT=5000"
User=root

[Install]
WantedBy=multi-user.target
```

4. **Enable and start:**
```bash
sudo systemctl enable agent
sudo systemctl start agent
```

## Testing

### Run Tests
```bash
pytest tests/
```

### Health Checks
```bash
# Check controller
curl http://localhost:8000/api/auth/login

# Check agent
curl http://localhost:5001/health

# Check database
curl http://localhost:5432 (psql -U compute_user -d compute_booking)
```

## Troubleshooting

### Agent not detected
- Ensure firewall allows port 5000 (or configured AGENT_PORT)
- Check network connectivity: `ping agent_ip`
- Verify health: `curl http://agent_ip:5000/health`

### Container fails to start
- Check image exists: `docker images | grep image_name`
- Verify Docker daemon running on agent
- Check resource availability: `docker stats`

### Database errors
- Ensure PostgreSQL is running and accessible
- Check connection string in DATABASE_URL
- Run migrations if needed

## Development

### Adding a new route
1. Create route in `controller/routes/`
2. Add schema in `controller/schemas.py` (for validation)
3. Add test in `tests/test_*.py`
4. Update README

### Adding agent endpoint
1. Add method to `agent/agent.py`
2. Update health check logic if needed
3. Update controller scheduler if calling it

## Contributing

1. Follow PEP 8 style guide
2. Add tests for new features
3. Update README with new endpoints
4. Commit with clear messages

## License

MIT

## Support

For issues and questions, please file an issue or contact the team.
