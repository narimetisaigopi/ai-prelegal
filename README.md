# Prelegal

Prelegal is a SaaS starter for drafting legal agreements via AI chat.

## Run with Docker

1. Copy `.env.example` to `.env` and fill `OPENROUTER_API_KEY`.
2. Start:

```bash
./scripts/start-mac.sh
```

3. Open `http://localhost:8000`.
4. Stop:

```bash
./scripts/stop-mac.sh
```

## Local development

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API endpoints

- `POST /api/auth/signup`
- `POST /api/auth/signin`
- `POST /api/auth/signout`
- `GET /api/auth/me`
- `GET /api/documents`
- `POST /api/documents`
- `GET /api/documents/{id}`
- `PUT /api/documents/{id}`
- `DELETE /api/documents/{id}`
- `GET /api/chat/greeting`
- `POST /api/chat/message`
- `GET /api/health`
