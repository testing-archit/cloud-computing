# Node Setup Guide

This guide walks through setting up a worker node (machine) to run compute booking agents.

## Prerequisites

- Linux (Ubuntu 20.04+ recommended) or macOS
- Docker installed and running
- Python 3.9+
- Static IP address
- Wake-on-LAN (WoL) capable motherboard (optional but recommended)

## Step 1: System Preparation

### On Linux (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group (allows running docker without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Install Python & Pip
sudo apt install python3 python3-pip -y

# Install system dependencies
sudo apt install curl wget git net-tools -y
```

### On macOS

```bash
# Install Docker (https://www.docker.com/products/docker-desktop)
# Then verify installation
docker --version

# Python3 usually comes pre-installed
python3 --version
```

## Step 2: Install Agent Dependencies

```bash
# Create agent directory
mkdir -p /opt/agent
cd /opt/agent

# Clone or copy agent files
# (Assuming you have the agent code)
cp /path/to/agent.py /opt/agent/

# Install Python dependencies
pip install flask docker requests psutil
```

## Step 3: Get Your Node Info

Collect the following information for registering with the controller:

```bash
# Get IP address
hostname -I | awk '{print $1}'
# or
ip addr show

# Get MAC address (replace eth0 with your interface)
ip link show eth0 | grep link/ether | awk '{print $2}'

# Check available resources
nproc  # CPU cores
free -g  # RAM in GB
```

## Step 4: Register Node with Controller

From the controller machine, add your node to the database:

```bash
# Connect to controller database
python3
```

```python
from controller.app import create_app, db
from controller.models import Agent

app = create_app()
with app.app_context():
    agent = Agent(
        name='Node 1',
        ip='192.168.1.100',  # Your node's static IP
        mac='00:11:22:33:44:55',  # Your MAC address
        port=5000,
        wol_enabled=True,
        total_cpu=8,  # Number of CPU cores
        available_cpu=8,
        total_mem=16,  # RAM in GB
        available_mem=16,
        tags='gpu,ml'  # Optional tags
    )
    db.session.add(agent)
    db.session.commit()
    print(f"Agent registered: {agent.id}")
```

Exit Python and continue.

## Step 5: Enable Wake-on-LAN (BIOS)

1. Restart your node and enter BIOS (usually F2, F10, DEL, or ESC during boot)
2. Look for Power Management or Advanced settings
3. Enable "Wake on LAN" or "WoL"
4. Save and exit

## Step 6: Configure Systemd Service (Linux)

Create `/etc/systemd/system/agent.service`:

```ini
[Unit]
Description=Compute Booking Agent
After=docker.service network.target
Wants=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/agent
ExecStart=/usr/bin/python3 /opt/agent/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="AGENT_HOST=192.168.1.100"
Environment="AGENT_PORT=5000"

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable agent
sudo systemctl start agent

# Check status
sudo systemctl status agent

# View logs
sudo journalctl -u agent -f
```

## Step 7: Create Docker Network

Create a shared network for Traefik routing (if not already done):

```bash
docker network create proxy || true
```

## Step 8: Test Agent Health

From controller or any machine on the network:

```bash
# Test health endpoint
curl http://192.168.1.100:5000/health

# Expected response:
# {
#   "status": "ok",
#   "host": "192.168.1.100",
#   "cpu_percent": 5.2,
#   "memory_percent": 42.1
# }
```

## Step 9: Network Configuration

### Static IP Assignment

**On Linux:**

Edit `/etc/netplan/00-installer-config.yaml`:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses: [192.168.1.100/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

Apply:
```bash
sudo netplan apply
```

**On macOS:**

System Preferences → Network → Advanced → TCP/IP → Manual

### Firewall Rules

Allow port 5000 (or your AGENT_PORT):

**Linux:**
```bash
sudo ufw allow 5000
sudo ufw reload
```

**macOS:**
System Preferences → Security & Privacy → Firewall Options

## Step 10: Verify Everything

From the controller:

```bash
# 1. Check agent is online
curl http://192.168.1.100:5000/health

# 2. Create a test booking (from controller)
# ... create and approve a booking ...

# 3. Check that container started on the agent
docker ps

# 4. View agent logs
sudo journalctl -u agent -n 50
```

## Troubleshooting

### Agent fails to start

```bash
# Check service status
sudo systemctl status agent

# View logs
sudo journalctl -u agent -n 100

# Manual test
python3 /opt/agent/agent.py
```

### Docker socket permission denied

```bash
sudo usermod -aG docker $USER
newgrp docker
sudo systemctl restart docker
```

### Network connectivity issues

```bash
# Test DNS
nslookup controller.example.com

# Test connectivity to controller
ping controller_ip
curl http://controller_ip:8000/api/auth/login

# Check firewall
sudo ufw status
```

### WoL not working

```bash
# Check WoL capability
ethtool eth0 | grep Wake

# Enable WoL (Linux)
sudo ethtool -s eth0 wol g
sudo ethtool eth0 | grep Wake  # Verify it's enabled

# Make persistent (add to /etc/network/interfaces or netplan)
```

### Container won't start

```bash
# Check available resources
free -h
df -h

# Check Docker logs
docker logs <container_id>

# Pull image manually
docker pull jupyter/notebook
```

## Production Checklist

- [ ] Node has static IP
- [ ] Node has static MAC address
- [ ] WoL enabled in BIOS
- [ ] Agent service auto-starts on reboot
- [ ] Docker daemon auto-starts
- [ ] Firewall allows port 5000
- [ ] Node registered in controller DB
- [ ] Health check passes
- [ ] Can successfully start a test container
- [ ] Monitoring/logging configured
- [ ] Backups configured
- [ ] Regular updates applied

## Advanced Configuration

### Resource Limits Per Container

Edit `agent/agent.py` to add custom resource constraints:

```python
container = client.containers.run(
    image,
    mem_limit=memory,
    memswap_limit=-1,
    cpu_quota=int(cpu * 100000),
    cpu_period=100000,
    ...
)
```

### Custom Tags for Node Targeting

Set tags when registering:

```python
agent = Agent(
    tags='gpu,ml,heavy-compute',
    ...
)
```

Then students can filter by tags when creating bookings.

### Node Monitoring

Set up monitoring with Prometheus:

```bash
pip install prometheus-client
```

Then export metrics from agent:

```python
from prometheus_client import Counter, Histogram

container_starts = Counter('container_starts', 'Total containers started')
container_duration = Histogram('container_duration_seconds', 'Container runtime')
```

## Support

For issues, check:
1. Agent logs: `sudo journalctl -u agent -f`
2. Docker logs: `docker logs <container>`
3. Network: `curl http://node_ip:5000/health`
4. Controller logs for scheduling errors
