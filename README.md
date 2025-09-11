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
- Make sure local ports 8000, 27017, 6379, 5672, and 15672 are free.


## 2) Configuration Overview
Configuration is driven by a single JSON file and several .env files referenced from it:

- settings/config.json — main config loader. It references:
  - settings/mongo.env — Mongo connection config
  - settings/redis.env — Redis connection config
  - settings/rabbitmq.env — RabbitMQ connection config
  - data/lang.json — messages map
  - Inline jwt settings (secret/algorithm/ttl/bcrypt rounds)

The application config schema (src/core/config.py) loads referenced files automatically. Relevant fields:

- jwt.secret_key — JWT signing secret (HS256 by default)
- jwt.ttl_minutes — Access token TTL in minutes
- redis: HOST, PORT, PASSWORD
- rabbit: HOST, PORT, USER, PASSWORD, EXCHANGE (defaults to "events")
- database (Mongo): HOST, PORT, MONGO_USER, MONGO_PASSWORD, MONGO_DB

Note: The env file keys are uppercased, but the config loader maps them for use internally.


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
  docker compose up --build

- Run in detached mode:
  docker compose up -d --build

Check container logs:
  docker compose logs -f event_service

Stop the stack:
  docker compose down

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
    {
      "email": "user@example.com",
      "username": "john_doe",
      "password": "StrongP@ssw0rd",
      "full_name": "John Doe"  // optional
    }
  - Constraints:
    - username: 3-50 chars, alphanumeric and underscore only; coerced to lowercase
    - password: at least 8 chars, must contain at least one uppercase, one digit, and one special character
  - 200 Response:
    {
      "id": "<object_id>",
      "email": "user@example.com",
      "username": "john_doe",
      "full_name": "John Doe"
    }

- POST /v1/auth/login
  - Body:
    {
      "username": "john_doe",  // or email
      "password": "StrongP@ssw0rd"
    }
  - 200 Response:
    {
      "access_token": "<JWT>"
    }

- GET /v1/auth/me
  - Headers:
    Authorization: Bearer <JWT>
  - 200 Response:
    {
      "email": "user@example.com",
      "username": "john_doe",
      "full_name": "John Doe"
    }

Events (prefix: /v1/events)
- POST /v1/events/
  - Headers: Authorization: Bearer <JWT>
  - Body:
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
  - Validation rules:
    - end_time must be after start_time
    - start_time/end_time must be in the future
  - 200 Response example:
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
  - Side effects:
    - Publishes an event to RabbitMQ exchange "events" with routing key "events.created" and JSON body:
      {
        "id": "<event_id>",
        "title": "Conference 2026",
        "action": "created",
        "timestamp": "2026-05-01T08:00:00.000000Z",
        "user_id": "<creator_user_id>"
      }

- GET /v1/events/{event_id}
  - Headers: Authorization: Bearer <JWT>
  - 200 Response: EventResponse (see example above)

- GET /v1/events/
  - Headers: Authorization: Bearer <JWT>
  - Query/Body: Uses a typed table request. With FastAPI default behavior, send as query params or JSON depending on your client; the model is:
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
  - 200 Response:
    {
      "page": 1,
      "pages": 3,
      "total_count": 25,
      "items": [ /* array of EventResponse */ ]
    }

- POST /v1/events/{event_id}/subscribe
  - Headers: Authorization: Bearer <JWT>
  - 200 Response: empty body (subscription acknowledged)

Note: update and delete endpoints are present in code but not yet implemented.


## 7) RabbitMQ and Redis
- RabbitMQ
  - Exchange: events (topic/direct as configured by application; see src/core/brokers/setup.py if present)
  - Routing keys used: events.created (on event creation)
  - Management UI: http://localhost:15672 (USER/PASSWORD from settings/rabbitmq.env)

- Redis
  - Exposed at redis://:<PASSWORD>@localhost:6379
  - Password is set from settings/redis.env (PASSWORD)


## 8) Environment Files (defaults)
- settings/mongo.env
  HOST=localhost
  PORT=27017
  MONGO_USER=user1
  MONGO_PASSWORD=user1
  MONGO_DB=main

- settings/redis.env
  HOST=127.0.0.1
  PORT=6379
  PASSWORD=1234

- settings/rabbitmq.env
  HOST=localhost
  PORT=5672
  USER=admin
  PASSWORD=admin
  EXCHANGE=events

You can modify these values to match your environment. The application reads settings/config.json via CONFIG_PATH.


## 9) Troubleshooting
- Ports already in use
  - Ensure 8000, 27017, 6379, 5672, and 15672 are available.

- Cannot connect to MongoDB/RabbitMQ/Redis
  - Review logs: docker compose logs -f <service>
  - Verify env files under settings/ and that they are mounted correctly.

- Unauthorized (401) responses
  - Ensure you include Authorization: Bearer <token> header for protected endpoints.
  - Obtain token via POST /api/v1/auth/login

- RabbitMQ management login fails
  - Confirm USER and PASSWORD in settings/rabbitmq.env; the entrypoint script exports them to RABBITMQ_DEFAULT_USER/PASS.


## 10) Development Notes
- Interactive docs: http://localhost:8000/api/v1/docs
- OpenAPI: http://localhost:8000/api/v1/openapi.json
- JWT algorithm: HS256 (configurable)

If you need to change the app configuration path inside the container, adjust the event_service environment variable CONFIG_PATH in compose.yaml.
