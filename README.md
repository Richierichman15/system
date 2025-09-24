# Solo Leveling System

A gamified productivity system inspired by the Solo Leveling anime/manga, built with React frontend and FastAPI backend.

## 🎮 Features

- **Character Profile**: Track your level, experience, and stats
- **Task Management**: Complete quests to gain experience and level up
- **Achievement System**: Unlock achievements as you progress
- **Goal Setting**: Set and track long-term objectives
- **AI Integration**: Generate tasks using AI assistance
- **World Map**: Visual representation of your progress

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

The easiest way to run the entire application:

```bash
# Clone the repository
git clone <repository-url>
cd system

# Start both frontend and backend
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

### Option 2: Development Mode with Docker

For development with hot reloading:

```bash
# Start with development frontend
docker-compose --profile dev up --build

# Access the application
# Frontend: http://localhost:3001 (dev mode)
# Backend: http://localhost:8000
```

### Option 3: Manual Setup

#### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

#### Backend Setup

```bash
# Navigate to server directory
cd server

# Create and activate virtual environment
python -m venv ../venv
source ../venv/bin/activate  # On Windows: ..\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python -m app.cli
```

The backend will be available at `http://localhost:8000`

#### Frontend Setup

```bash
# Navigate to client directory (in a new terminal)
cd client

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🛠️ Development

### Backend Development

The backend is built with FastAPI and includes:

- **API Endpoints**: RESTful API for all features
- **Database**: SQLite with SQLModel ORM
- **AI Integration**: Ollama integration for task generation
- **CORS**: Configured for frontend communication

Key files:
- `server/app/main.py` - FastAPI application setup
- `server/app/routes/` - API route handlers
- `server/app/models.py` - Database models
- `server/app/db.py` - Database configuration

### Frontend Development

The frontend is built with React and Vite:

- **React Router**: Navigation between pages
- **Axios**: HTTP client for API communication
- **CSS Modules**: Component-specific styling

Key files:
- `client/src/App.jsx` - Main application component
- `client/src/pages/` - Page components
- `client/src/components/` - Reusable components
- `client/src/api.js` - API client configuration

### Available Scripts

#### Backend
```bash
# Start development server
python -m app.cli

# Run with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint
```

## 🐳 Docker Commands

### Production Deployment
```bash
# Build and run production containers
docker-compose -f docker-compose.prod.yml up --build
```

### Development with Hot Reload
```bash
# Run with development frontend
docker-compose --profile dev up --build
```

### Individual Services
```bash
# Run only backend
docker-compose up backend

# Run only frontend
docker-compose up frontend
```

## 📁 Project Structure

```
system/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── api.js         # API client
│   │   └── App.jsx        # Main app component
│   ├── Dockerfile         # Production build
│   ├── Dockerfile.dev     # Development build
│   └── package.json
├── server/                # FastAPI backend
│   ├── app/
│   │   ├── routes/        # API routes
│   │   ├── models.py      # Database models
│   │   ├── main.py        # FastAPI app
│   │   └── cli.py         # CLI entry point
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml     # Standard deployment
├── docker-compose.prod.yml # Production deployment
└── README.md
```

## 🔧 Configuration

### Environment Variables

#### Backend
- `DATABASE_URL`: Database connection string (default: `sqlite:///./data/system.db`)
- `CORS_ORIGINS`: Allowed CORS origins (default: `http://localhost:3000,http://localhost:80`)

#### Frontend
- `VITE_API_URL`: Backend API URL (default: `http://localhost:8000`)

### API Endpoints

- `GET /health` - Health check
- `GET /profile` - Get user profile
- `PATCH /profile` - Update user profile
- `GET /tasks` - List tasks
- `POST /tasks` - Create task
- `PATCH /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task
- `GET /achievements` - List achievements
- `GET /goals` - List goals
- `POST /goals` - Create goal
- `POST /ai/generate` - Generate tasks with AI

## 🐛 Troubleshooting


## 🧩 MCP Server (Jarvis)

Expose System functionality via Model Context Protocol (MCP) for your Jarvis client.

- Entrypoint: `system_server.py`
- Requires: Python 3.11+, installed backend deps (`server/requirements.txt`) and the `mcp` Python package

### Run locally

```bash
pip install -r server/requirements.txt
pip install mcp
python system_server.py
```

This launches an MCP stdio server.

### Connect from Jarvis

In your Jarvis client, connect via stdio:

```
connect system "python ../System/system_server.py"
```

Then call tools, for example:

```
system.add_goal {"title":"BMW 335i","target":12000}
system.check_progress {"title":"BMW 335i"}
system.get_status
```

Notes:
- Goals are stored in the existing database (`server/app/models.Goal`). The numeric `target` is saved inside the goal's `description` field as JSON (e.g., `{ "target": 12000 }`).
- `system.get_status` summarizes XP, active quests (Tasks marked active and not completed), and active goals for user `id=1`.

### Common Issues

#### Port Conflicts
- Backend runs on port 8000
- Frontend runs on port 3000 (production) or 3001 (development)
- Make sure these ports are available

#### CORS Errors
- Ensure the frontend URL matches the CORS configuration in the backend
- Check that the API_URL in `client/src/api.js` points to the correct backend URL

#### Database Issues
- The SQLite database is automatically created on first run
- Database file is located at `server/system.db`
- In Docker, the database is persisted in a volume

#### Build Issues
If you encounter rollup build issues:

```bash
cd client
./build-ci.sh
```

Or manually:
```bash
cd client
rm -rf node_modules package-lock.json
npm install --no-optional --legacy-peer-deps
npm run build
```

### Logs

#### Docker Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
```

#### Manual Setup Logs
- Backend logs are printed to the console
- Frontend logs are available in the browser developer tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

