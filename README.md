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
pytest

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

## Six-Step Improvement Loop

Tasks can iterate through a dedicated improvement loop to address feedback and
quality issues. The loop follows these high level stages:

1. **Checkpoint output** – after a task runs, its result is submitted for human
   review.
2. **Feedback tasks** – if changes are requested a new follow‑up task is
   created automatically.
3. **Controlled iteration** – each execution increments the
   `iteration_count` field and is checked against the task's `max_iterations`
   limit.
4. **Refresh dependencies** – dependent tasks are marked as `stale` so they are
   revisited with the new information.
5. **QA gate** – final approval of the output before completion.
6. **Close loop** – once approved the iteration counter resets to zero.

### API endpoints

The backend exposes a small API to manage this loop:

- `POST /improvement/start/{task_id}` – submit output for review.
- `GET /improvement/status/{task_id}` – retrieve the current iteration count and
  configured limit.
- `POST /improvement/close/{task_id}` – clear the loop state once approved.

Use the status endpoint to monitor how many iterations have occurred and to
detect when the `max_iterations` threshold has been exceeded.

