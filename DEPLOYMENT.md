# Deployment Guide

This guide covers different deployment approaches for the Solo Leveling System, including fixes for the rollup CI/CD issue.

## 🐳 Docker Deployment

### Production Deployment
```bash
# Build and run production containers
docker-compose -f docker-compose.prod.yml up --build

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Development Deployment
```bash
# Run with development frontend (includes rollup fix)
docker-compose --profile dev up --build

# Access the application
# Frontend: http://localhost:3001 (dev mode)
# Backend: http://localhost:8000
```

### Standard Deployment
```bash
# Run standard containers
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 🔧 Manual Build (Rollup Fix)

If you encounter rollup issues, use these approaches:

### Option 1: Use the CI Build Script
```bash
cd client
./build-ci.sh
```

### Option 2: Manual Commands
```bash
cd client
rm -rf node_modules package-lock.json
npm install --no-optional --legacy-peer-deps
npm run build
```

### Option 3: Use npm script
```bash
cd client
npm run build:ci
```

## 🚀 CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically:
1. Tests the backend
2. Builds the frontend with rollup fixes
3. Builds Docker images
4. Deploys to production (on main branch)

## 🛠️ Troubleshooting

### Rollup Error: "Cannot find module @rollup/rollup-linux-x64-gnu"
This is fixed by:
- Using the CI build script
- Adding explicit rollup dependencies
- Using `--no-optional` flag during npm install

### CORS Issues
- Backend runs on port 8000
- Frontend runs on port 3000 (production) or 3001 (development)
- CORS is configured for both ports

### Database Issues
- SQLite database is persisted in Docker volumes
- Database schema is automatically created on startup

## 📁 File Structure

```
system/
├── client/
│   ├── Dockerfile              # Production build
│   ├── Dockerfile.dev          # Development build with rollup fix
│   ├── build-ci.sh            # CI build script
│   ├── .npmrc                 # npm configuration
│   └── package.json           # Updated with rollup dependencies
├── server/
│   └── Dockerfile             # Backend container
├── docker-compose.yml         # Standard deployment
├── docker-compose.prod.yml    # Production deployment
└── .github/workflows/ci.yml   # CI/CD pipeline
```

## 🎯 Quick Start

1. **Clone the repository**
2. **Choose your deployment method:**
   - Production: `docker-compose -f docker-compose.prod.yml up --build`
   - Development: `docker-compose --profile dev up --build`
   - Manual: Follow the manual build steps above

3. **Access the application:**
   - Frontend: http://localhost:3000 (or 3001 for dev)
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
