# PiGenus Deployment Guide

## Prerequisites

### Hardware
- **Raspberry Pi 5** (recommended)
- **8GB RAM** (recommended)
- **USB SSD** (recommended for database)
- **Ethernet connection** (recommended for reliability)

### Software
- **Raspberry Pi OS** (64-bit recommended)
- **Python 3.12+**
- **Git**

---

## Installation

### 1. Clone the Repository
```bash
cd /home/pi
git clone https://github.com/WoltLab51/PiGenus_mistral.git
cd PiGenus_mistral
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
nano .env
```

Edit the `.env` file with your settings:
```ini
# Database
DATABASE_URL=sqlite:////home/pi/PiGenus_mistral/pigenus.db

# Security
SECRET_KEY=your-very-secure-random-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Worker
WORKER_LEASE_TIMEOUT=60

# Scheduler
NIGHTLY_JOBS_HOUR=3
```

Generate a secure `SECRET_KEY`:
```bash
openssl rand -hex 32
```

### 5. Initialize Database
```bash
python scripts/init_db.py
```

This will:
- Create all database tables
- Create a test admin user (if `DEBUG=True` or `CREATE_TEST_ADMIN=true`)

---

## Running PiGenus

### Development Mode
```bash
uvicorn api.main:app --reload
```

- Runs on `http://0.0.0.0:8000`
- Auto-reloads on code changes
- For development only

### Production Mode
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

- Runs without reload
- Use systemd for production (recommended)

---

## systemd Deployment

### 1. Copy Service Files
```bash
sudo cp systemd/pigenus.service /etc/systemd/system/
sudo cp systemd/pigenus-scheduler.service /etc/systemd/system/
```

### 2. Edit Service Files (if needed)
Edit the paths in the service files to match your installation:
```bash
sudo nano /etc/systemd/system/pigenus.service
```

Update:
- `WorkingDirectory`
- `EnvironmentFile`
- `User` and `Group` (if not `pi`)

### 3. Enable and Start Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable pigenus
sudo systemctl enable pigenus-scheduler

# Start services
sudo systemctl start pigenus
sudo systemctl start pigenus-scheduler
```

### 4. Check Service Status
```bash
# Check main service
sudo systemctl status pigenus

# Check scheduler service
sudo systemctl status pigenus-scheduler

# View logs
journalctl -u pigenus -f
journalctl -u pigenus-scheduler -f
```

---

## Reverse Proxy (Optional)

### nginx Configuration
```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/pigenus
```

Add:
```nginx
server {
    listen 80;
    server_name pigenus.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/pigenus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d pigenus.yourdomain.com
```

---

## Firewall Configuration

Allow necessary ports:
```bash
sudo ufw allow 22/tcp       # SSH
sudo ufw allow 80/tcp       # HTTP
sudo ufw allow 443/tcp      # HTTPS
sudo ufw allow 8000/tcp     # PiGenus API (if not using reverse proxy)
sudo ufw enable
```

---

## Private Network Access

### Option 1: Tailscale (Recommended)
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

- Creates a private VPN
- Workers can connect to PiGenus via Tailscale IP
- No port forwarding needed

### Option 2: WireGuard
```bash
sudo apt install wireguard
wg genkey | sudo tee /etc/wireguard/privatekey | wg pubkey | sudo tee /etc/wireguard/publickey
```

Configure `/etc/wireguard/wg0.conf` and enable IP forwarding.

---

## Updating PiGenus

### 1. Pull Latest Changes
```bash
cd /home/pi/PiGenus_mistral
git pull origin main
```

### 2. Update Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations (if any)
```bash
# Currently using SQLite, no migrations needed
# For future PostgreSQL: alembic upgrade head
```

### 4. Restart Services
```bash
sudo systemctl restart pigenus
sudo systemctl restart pigenus-scheduler
```

---

## Backup

### Database Backup
```bash
# Manual backup
sqlite3 /home/pi/PiGenus_mistral/pigenus.db .dump > pigenus_backup_$(date +%Y-%m-%d).sql

# Automated (via cron)
0 2 * * * sqlite3 /home/pi/PiGenus_mistral/pigenus.db .dump > /backup/pigenus_$(date +\%Y-\%m-\%d).sql
```

### Full Backup
```bash
# Backup entire directory
tar -czvf pigenus_full_backup_$(date +%Y-%m-%d).tar.gz /home/pi/PiGenus_mistral
```

---

## Monitoring

### Check API Health
```bash
curl http://localhost:8000/health
```

### View Logs
```bash
# API logs
journalctl -u pigenus -f

# Scheduler logs
journalctl -u pigenus-scheduler -f

# Application logs (if configured)
tail -f /var/log/pigenus.log
```

### System Metrics
```bash
# CPU, Memory, Disk
top
h top
df -h

# Network
iftop
```

---

## Troubleshooting

### Common Issues

1. **Database not found**
   - Ensure `DATABASE_URL` in `.env` points to the correct path
   - Run `python scripts/init_db.py`

2. **Permission denied**
   - Check file permissions: `chmod 600 pigenus.db`
   - Check directory permissions: `chmod 700 /home/pi/PiGenus_mistral`

3. **Port already in use**
   - Check with: `sudo lsof -i :8000`
   - Kill process: `sudo kill <PID>`

4. **Module not found**
   - Activate virtual environment: `source venv/bin/activate`
   - Reinstall dependencies: `pip install -r requirements.txt`

5. **systemd service fails**
   - Check logs: `journalctl -u pigenus -xe`
   - Test manually: `python -m uvicorn api.main:app --host 0.0.0.0 --port 8000`

### Debug Mode
Enable debug mode in `.env`:
```ini
DEBUG=True
```

Then check logs for detailed error messages.

---

## Scaling

### Multiple Workers
1. Register each worker with a unique name
2. Workers automatically receive jobs via `/jobs/lease`
3. Monitor worker status in `/admin/status`

### Multiple PiGenus Nodes (Future)
- Use PostgreSQL instead of SQLite
- Implement leader election
- Use Redis for job queue
- Add health checks between nodes

---

## Security Checklist

- [ ] Change default `SECRET_KEY`
- [ ] Disable `DEBUG=True` in production
- [ ] Set proper file permissions (`chmod 600 .env pigenus.db`)
- [ ] Use HTTPS (via reverse proxy)
- [ ] Enable firewall (`ufw`)
- [ ] Use private network (Tailscale/WireGuard)
- [ ] Regular backups
- [ ] Monitor logs for suspicious activity
- [ ] Rotate `SECRET_KEY` periodically
- [ ] Use strong passwords for all users
