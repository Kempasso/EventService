# TestProject — Docker Compose Deployment Guide

This document explains how to run the application stack with Docker Compose and describes the key API endpoints and the data they expect.

The stack includes:
- FastAPI application (Events Service)
- MongoDB (data store)
- Redis (caching / pub-sub helper)
- RabbitMQ (event broker with management UI)

The application exposes interactive API docs at: http://localhost:8000/api/v1/docs


## 1) Prerequisites
- Docker (https://docs.docker.com/get-docker/)
- Docker Compose (v2+, typically bundled with Docker Desktop)

Optional (for development):
- Make sure local ports 8000, 9000, 27017, 6379, 5672, and 15672 are free.


## 2) Configuration Overview
Configuration is driven by a single JSON file and several .env files referenced from it:

- settings/config.json — main config loader. It references:
  - settings/mongo.env — Mongo connection config
  - settings/redis.env — Redis connection config
  - settings/rabbitmq.env — RabbitMQ connection config
  - data/lang.json — messages map

I deliberately left the configs with test data in Git so that there would be no need to bother with setup!!!!!!!!!

## 3) Running with Docker Compose

Compose file: compose.yaml

Services:
- mongodb
  - Image: mongo:7
  - Ports: 27017 -> 27017
  - Env file: settings/mongo.env
  - Volume: named volume mongo_data for data persistence
  - Entrypoint script: scripts/setup_mongo.sh (exports MONGO_INITDB_*)

- rabbitmq
  - Image: rabbitmq:3.13-management
  - Ports: 5672 (AMQP), 15672 (management UI)
  - Env file: settings/rabbitmq.env
  - Volume: named volume rabbitmq_data
  - Entrypoint script: scripts/setup_rabbit.sh (sets default user/pass)
  - Management UI: http://localhost:15672 (login: USER/PASSWORD from settings/rabbitmq.env)

- redis
  - Image: redis:latest
  - Port: 6379
  - Env file: settings/redis.env
  - Volume: redis_data for persistence
  - Entrypoint script: scripts/setup_redis.sh (enables password)

- event_service (FastAPI app)
  - Build: Dockerfile in repository root
  - Ports: 8000 -> 8000
  - Environment: CONFIG_PATH=/app/settings/config.json
  - Mounts: settings folder (read-only) into /app/settings
  - Depends on: mongodb, rabbitmq, redis

Start the stack:

- Build and run in the foreground:

```bash
  docker compose up --build
```
- Run in detached mode:
```bash
  docker compose up -d --build
```


Persistent data volumes created by compose:
- mongo_data
- rabbitmq_data
- redis_data


## 4) Application Access
- FastAPI app base URL: http://localhost:8000
- API base path: /api
- OpenAPI (JSON): /api/v1/openapi.json
- Swagger UI: /api/v1/docs


## 5) Authentication & Headers
Protected endpoints require a Bearer token in the Authorization header. Acquire the token via the login endpoint, then pass it like:
Authorization: Bearer <access_token>


## 6) API Endpoints and Payloads
Below are the key endpoints and the data they expect. All paths are relative to the application base path /api.

Auth (prefix: /v1/auth)
- POST /v1/auth/register
  - Body (application/json):
  ```json
    {
      "email": "user@example.com",
      "username": "john_doe",
      "password": "StrongP@ssw0rd",
      "full_name": "John Doe"  // optional
    }
    ```
  - 200 Response:
  ```json
    {
      "id": "<object_id>",
      "email": "user@example.com",
      "username": "john_doe",
      "full_name": "John Doe"
    }
    ```

- POST /v1/auth/login
  - Body:
  ```json
    {
      "username": "john_doe",  // or email
      "password": "StrongP@ssw0rd"
    }
    ```
  - 200 Response:
  ```json
    {
      "access_token": "<JWT>"
    }
    ```

- GET /v1/auth/me
  - Headers:
    Authorization: Bearer <JWT>
  
  - 200 Response:
  ```json
    {
      "email": "user@example.com",
      "username": "john_doe",
      "full_name": "John Doe"
    }
    ```

Events (prefix: /v1/events)
- POST /v1/events/
  - Headers: Authorization: Bearer <JWT>
  - Body:
  ```json
    {
      "title": "Conference 2026",
      "description": "Annual tech conference",
      "location": "Berlin",
      "start_time": "2026-05-01T09:00:00Z",  // ISO 8601; naive is coerced to UTC
      "end_time": "2026-05-01T18:00:00Z",
      "tags": ["tech", "networking"],
      "max_attendees": 250,
      "status": "scheduled"  // scheduled|... (see EventStatus enum)
    }
    ```
  - Validation rules:
    - end_time must be after start_time
    - start_time/end_time must be in the future
  
  - 200 Response:
  ```json
    {
      "id": "<object_id>",
      "title": "Conference 2026",
      "description": "Annual tech conference",
      "location": "Berlin",
      "start_time": "2026-05-01T09:00:00+00:00",
      "end_time": "2026-05-01T18:00:00+00:00",
      "created_by": { "email": "...", "username": "...", "full_name": "..." },
      "tags": ["tech", "networking"],
      "max_attendees": 250,
      "status": "scheduled"
    }
    ```
  - Side effects:
    - Publishes an event to RabbitMQ exchange "events" with routing key "events.created" and JSON body:
  ```json
      
       {
        "id": "<event_id>",
        "title": "Conference 2026",
        "action": "created",
        "timestamp": "2026-05-01T08:00:00.000000Z",
        "user_id": "<creator_user_id>"
      }
  ```

- GET /v1/events/{event_id}
  - Headers: Authorization: Bearer <JWT>
  - 200 Response: EventResponse (see example above)

- GET /v1/events/
  - Headers: Authorization: Bearer <JWT>
  - Query/Body: Uses a typed table request. With FastAPI default behavior, send as query params or JSON depending on your client; the model is:
  ```json
      
       {
      "filters": {
        "start_time": {"min": "<ISO-datetime>", "max": "<ISO-datetime>"},
        "end_time":   {"min": "<ISO-datetime>", "max": "<ISO-datetime>"}
      },
      "order": [{"column": "start_time", "ascending": true}],
      "page": 1,
      "page_size": 10,
      "sort_by": "start_time",
      "sort_order": "asc"  // or "desc"
    }
     ```
  - 200 Response:
  ```json
    {
      "page": 1,
      "pages": 3,
      "total_count": 25,
      "items": [ /* array of EventResponse */ ]
    }
    ```

- POST /v1/events/{event_id}/subscribe
  - Headers: Authorization: Bearer <JWT>
  - 200 Response: empty body (subscription acknowledged)