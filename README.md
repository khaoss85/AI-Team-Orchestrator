# AI Team Orchestrator

AI Team Orchestrator is a platform for managing teams of cooperating AI agents. The backend is built with **FastAPI** while the frontend uses **Next.js**. The application relies on Supabase for persistence and the OpenAI Agents SDK for AI capabilities.

## Folder Structure

- `backend/` – FastAPI server and agent logic
- `frontend/` – Next.js application

## Setup

### Requirements

- Node.js 18+
- Python 3.11+

### Installation

```bash
# install Python dependencies
cd backend
pip install -r requirements.txt

# install Node dependencies
cd ../frontend
npm install
```

### Environment variables

Create a `backend/.env` file and define at least the following variables:

- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`

Other optional variables are available in the backend configuration. Example usage of these variables can be seen in `backend/deliverable_aggregator.py` and `backend/database.py`.

To enable a simpler asset-oriented output you can set the following in your `.env`:

```bash
USE_ASSET_FIRST_DELIVERABLE=true
```

This will create deliverables that prioritise immediately usable assets.

### Running

Start the backend:

```bash
cd backend
python main.py
```

Start the frontend:

```bash
cd frontend
npm run dev
```

