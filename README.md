# 🎙️ Podcast Digest

A full-stack web application that processes English podcasts, generates Mandarin summaries using AI, and sends weekly newsletters to subscribers.

## Features

- **Podcast Processing**: Automatically downloads and processes podcasts from RSS feeds
- **AI Transcription**: Uses OpenAI Whisper API for accurate speech-to-text conversion
- **Smart Translation**: GPT-4 powered summarization and translation to Mandarin Chinese
- **Email Newsletter**: Weekly digest sent via Beehiiv platform
- **Modern UI**: React frontend with Tailwind CSS for podcast discovery and subscription
- **Background Processing**: Celery-based task queue for handling audio processing
- **Railway Deployment**: Ready for cloud deployment

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Database for storing podcasts and episodes
- **SQLAlchemy** - ORM for database operations
- **Celery + Redis** - Background task processing
- **OpenAI APIs** - Whisper (transcription) and GPT-4 (summarization/translation)

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client for API calls

### External Services
- **Beehiiv** - Newsletter platform and email delivery
- **Railway** - Cloud deployment platform

## Project Structure

```
pod_digest/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Business logic services
│   │   ├── models.py       # Database models
│   │   ├── config.py       # Configuration settings
│   │   ├── database.py     # Database connection
│   │   ├── main.py         # FastAPI application
│   │   └── tasks.py        # Celery background tasks
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile         # Backend container
│   └── init_data.py       # Sample data initialization
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API client
│   │   └── App.tsx        # Main application
│   ├── package.json       # Node dependencies
│   └── Dockerfile         # Frontend container
├── railway.toml           # Railway deployment config
└── README.md              # This file
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database
- Redis server
- OpenAI API key
- Beehiiv account and API key

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/pod_digest

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Beehiiv
BEEHIIV_API_KEY=your_beehiiv_api_key_here
BEEHIIV_PUBLICATION_ID=your_beehiiv_publication_id_here

# Redis
REDIS_URL=redis://localhost:6379

# App
FRONTEND_URL=http://localhost:3000
DEBUG=False
```

### Local Development

1. **Backend Setup**:
```bash
cd backend
pip install -r requirements.txt
python init_data.py  # Initialize sample data
uvicorn app.main:app --reload --port 8000
```

2. **Start Celery Worker** (in separate terminal):
```bash
cd backend
celery -A app.tasks worker --loglevel=info
```

3. **Start Celery Beat** (in separate terminal):
```bash
cd backend
celery -A app.tasks beat --loglevel=info
```

4. **Frontend Setup**:
```bash
cd frontend
npm install
npm start
```

5. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Endpoints

- `GET /api/podcasts` - Get featured podcasts
- `GET /health` - Health check endpoint
- `GET /` - API root

## How It Works

1. **RSS Processing**: Celery tasks automatically fetch new episodes from configured RSS feeds
2. **Audio Processing**: Downloads MP3 files and transcribes them using OpenAI Whisper
3. **Content Generation**: GPT-4 creates concise summaries and translates them to Mandarin
4. **Newsletter Creation**: Weekly Celery Beat task aggregates summaries and creates Beehiiv newsletters
5. **Email Delivery**: Beehiiv handles email delivery to subscribers

## Deployment

### Railway Deployment

1. **Connect your GitHub repository** to Railway
2. **Add environment variables** in Railway dashboard
3. **Add PostgreSQL and Redis** add-ons
4. **Deploy** - Railway will automatically detect and deploy both services

The application is configured to run multiple services:
- Web service (FastAPI backend)
- Worker service (Celery worker)
- Beat service (Celery scheduler)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
