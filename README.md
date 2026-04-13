# Frontend-Backend Integration Framework

> This project demonstrates backend system design concepts including APIs, data processing, and asynchronous workflows.

## Overview

A reusable Flask + JavaScript template for building frontend-backend integrated apps. Covers CRUD REST APIs, input validation, structured JSON responses, async form submission, and error handling — so projects start with a solid working foundation instead of from scratch.

## Purpose

This template was created to standardize frontend-backend integration using Flask REST APIs and JavaScript Fetch.

While building the [distributed-task-queue](https://github.com/Madhu0568/distributed-task-queue) and [student-analytics-platform](https://github.com/Madhu0568/student-analytics-platform) projects, I found myself rewriting the same boilerplate every time — input validation, error response formatting, async form submission with no page reload. I extracted all of that into a reusable template so future projects could start with a solid, working foundation instead of from zero.

It was reused across multiple projects including:
- [distributed-task-queue](https://github.com/Madhu0568/distributed-task-queue) — task submission forms and status polling
- [student-analytics-platform](https://github.com/Madhu0568/student-analytics-platform) — student record forms and async dashboard loading

## What it includes

- **CRUD REST API** built with Flask — Create, Read, Update, Delete with proper HTTP status codes
- **Input validation middleware** — required fields, string length, email format, JSON content-type check
- **Structured JSON response contracts** — consistent `{success, data, message, timestamp}` format for all responses
- **Error handling** — centralized handlers for 400 (validation), 404 (not found), 415 (wrong content-type), 500 (server error)
- **Async form handling** with JavaScript Fetch API — zero page reloads on submit
- **Pagination, filtering, and sorting** on the list endpoint
- **Batch creation** endpoint — submit multiple items in one request with per-item error tracking
- `@require_json` decorator — reusable middleware that validates content-type before route logic

## Tech Stack

Python · Flask · JavaScript (Fetch API) · HTML5 · CSS3

## How to Run

```bash
pip install -r requirements.txt
python app.py
```

Opens at `http://localhost:5004`.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/items` | Create an item |
| GET | `/api/items` | List items (params: `category`, `search`, `sort`, `order`, `page`, `per_page`) |
| GET | `/api/items/<id>` | Get single item |
| PUT | `/api/items/<id>` | Update an item |
| DELETE | `/api/items/<id>` | Delete an item |
| POST | `/api/items/batch` | Create multiple items with per-item error reporting |
| GET | `/api/stats` | Count by category |
| GET | `/api/health` | Health check |

## Response Format

Every endpoint returns the same structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Item created successfully",
  "timestamp": "2024-11-14T10:23:41"
}
```

Errors return:
```json
{
  "error": "Missing required fields: name",
  "field": "name",
  "type": "validation_error"
}
```

## Example

```bash
# Create an item
curl -X POST http://localhost:5004/api/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Flask Tutorial", "category": "education", "email": "user@example.com"}'

# List with filter + pagination
curl "http://localhost:5004/api/items?category=education&page=1&per_page=10"

# Batch create
curl -X POST http://localhost:5004/api/items/batch \
  -H "Content-Type: application/json" \
  -d '{"items": [{"name": "Item A"}, {"name": "B"}, {"name": "Item C"}]}'
# Response includes which ones failed validation and why
```

## Validation Rules

| Field | Rule |
|-------|------|
| `name` | Required, 2–100 characters |
| `email` | Optional, validated against regex `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` |
| Content-Type | Must be `application/json` for POST/PUT — returns 415 otherwise |

## How to extend this template

1. Replace the in-memory `items_db` dict with a real database (SQLite, PostgreSQL)
2. Add authentication middleware (API key header check or session)
3. Add more field types to the validator
4. Swap the frontend for a React or Vue component

This is intentionally minimal — it's a starting point, not a finished product.

## Output

See [sample_output.txt](sample_output.txt) for real API request/response examples including CRUD operations, validation errors, and health check output.
