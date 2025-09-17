# System Project Capabilities

## Core Functionality

### AI-Powered Task Generation
- Creates personalized daily/weekly/monthly tasks based on user goals
- Uses TinyLlama model for fast generation
- Implements caching to improve performance
- Provides fallback tasks if AI fails

### Task Management
- Displays tasks in a cyberpunk-styled interface
- Allows completing tasks to earn XP
- Filters tasks by status (all/active/completed)

### Profile & Progress Tracking
- Tracks user XP and level
- Automatically awards skill points (1 per 100 XP)
- Displays stats in a persistent header

### Navigation
- Game-like dashboard/start menu
- Navigation between different sections
- "Main Menu" button for easy return to dashboard

### User Interface
- Cyberpunk/sci-fi themed styling
- Animated elements and transitions
- Loading indicators for async operations

## Technical Features

### Frontend (React)
- Component-based architecture
- React Router for navigation
- Responsive design
- API client for backend communication

### Backend (FastAPI)
- RESTful API endpoints
- Database integration with SQLModel
- AI integration with Ollama
- Rate limiting for API requests

### Performance Optimizations
- Response caching
- Optimized AI model parameters
- Background model warming
