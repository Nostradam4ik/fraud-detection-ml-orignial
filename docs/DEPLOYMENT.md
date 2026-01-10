# Deployment Guide

## Quick Deploy Options

### Railway (Recommended)

1. **Connect Repository**
   - Go to [Railway.app](https://railway.app)
   - Create new project from GitHub repo
   - Select MoneyPrint repository

2. **Configure Backend**
   ```bash
   # Root directory: /backend
   # Build command: pip install -r requirements.txt
   # Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Environment Variables**
   ```
   SECRET_KEY=your-secure-secret-key
   DEBUG=false
   DATABASE_URL=postgresql://...
   CORS_ORIGINS=https://your-frontend.railway.app
   ```

4. **Configure Frontend**
   ```bash
   # Root directory: /frontend
   # Build command: npm install && npm run build
   # Start command: npx serve dist -s
   ```

5. **Set Frontend Environment**
   ```
   VITE_API_URL=https://your-backend.railway.app/api/v1
   ```

---

### Docker Compose (Self-hosted)

```bash
# Clone repository
git clone https://github.com/yourusername/MoneyPrint.git
cd MoneyPrint

# Create .env file
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=false
CORS_ORIGINS=http://localhost:3000
EOF

# Start services
docker-compose up -d
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
```

---

### Render

**Backend Service:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Root Directory: `backend`

**Frontend Static Site:**
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Root Directory: `frontend`

---

## Environment Variables

### Backend

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | JWT signing key | Yes | - |
| `DEBUG` | Debug mode | No | `true` |
| `DATABASE_URL` | Database connection | No | SQLite |
| `CORS_ORIGINS` | Allowed origins | No | `*` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `RATE_LIMIT` | Requests/minute | No | `100` |

### Frontend

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | Backend API URL | Yes |

---

## Database Setup

### SQLite (Default)
No configuration needed. Database file created automatically.

### PostgreSQL (Production)
```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

---

## SSL/TLS

Railway and Render provide automatic HTTPS.

For self-hosted:
```bash
# Using Caddy (automatic HTTPS)
caddy reverse-proxy --from yourdomain.com --to localhost:8000
```

---

## Monitoring

### Health Check
```bash
curl https://your-api.com/api/v1/health
```

### Prometheus Metrics
Configure in `monitoring/prometheus.yml`

### Logs
```bash
# Railway
railway logs

# Docker
docker-compose logs -f backend
```

---

## Backup

### Database
```bash
# SQLite
cp fraud_detection.db fraud_detection.db.backup

# PostgreSQL
pg_dump $DATABASE_URL > backup.sql
```

### ML Model
```bash
cp -r ml/models/ backups/models_$(date +%Y%m%d)/
```

---

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
```

### Load Balancing
Use Nginx or cloud provider load balancer.

---

## Troubleshooting

### Model Not Loading
```bash
# Train model
cd backend
python -m ml.train
```

### Database Errors
```bash
# Reset database
rm fraud_detection.db
# Restart backend
```

### CORS Issues
Ensure `CORS_ORIGINS` includes your frontend URL.

---

## Security Checklist

- [ ] Change default `SECRET_KEY`
- [ ] Set `DEBUG=false` in production
- [ ] Use HTTPS
- [ ] Configure rate limiting
- [ ] Set proper CORS origins
- [ ] Enable security headers (automatic)
- [ ] Regular backups
- [ ] Monitor logs
