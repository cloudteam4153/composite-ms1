# Composite Microservice (composite-ms1)

A composite microservice that encapsulates and coordinates all atomic microservices in the unified inbox system.

## Overview

This service acts as a gateway/orchestrator that:
- Delegates API requests to appropriate atomic microservices
- Implements parallel execution for concurrent service calls
- Validates logical foreign key constraints across services
- Coordinates database connectivity across all services
- Provides monitoring and logging for inter-service communication

## Architecture

The composite service coordinates three atomic microservices:

1. **Integrations Service** (port 8000) - External resource integration, Gmail, OAuth
2. **Actions Service** (port 8004) - Task management, todos, follow-ups
3. **Classification Service** (port 8001) - AI-powered message classification and prioritization

## Features

### 1. API Delegation
All endpoints from atomic services are exposed through the composite service with the prefix `/api/{service}`:
- `/api/integrations/*` - Routes to integrations service
- `/api/actions/*` - Routes to actions service
- `/api/classification/*` - Routes to classification service

### 2. Parallel Execution
The service uses `asyncio.gather()` for parallel execution when multiple service calls are needed, improving performance for composite operations.

### 3. Foreign Key Validation
Logical foreign key constraints are validated across services:
- User existence validation
- Connection ownership validation
- Message ownership validation
- Classification existence validation
- Task existence validation

### 4. Database Coordination
The service provides utilities to:
- Check health of all atomic services
- Monitor database connectivity across services
- Coordinate database operations

### 5. Monitoring & Logging
- Comprehensive logging of all inter-service communication
- Request/response logging with service names
- Error tracking and reporting
- Health check aggregation

## Setup

### Prerequisites
- Python 3.9+
- All atomic microservices running and accessible

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (optional, defaults provided):
```bash
export INTEGRATIONS_SERVICE_URL=http://localhost:8000
export ACTIONS_SERVICE_URL=http://localhost:8004
export CLASSIFICATION_SERVICE_URL=http://localhost:8001
export FASTAPIPORT=8002
export REQUEST_TIMEOUT=30
export LOG_LEVEL=INFO
```

Or create a `.env` file:
```
INTEGRATIONS_SERVICE_URL=http://localhost:8000
ACTIONS_SERVICE_URL=http://localhost:8004
CLASSIFICATION_SERVICE_URL=http://localhost:8001
FASTAPIPORT=8002
REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
```

3. Run the service:
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## API Endpoints

### Health Check
- `GET /health` - Check composite service and all atomic services health

### Integrations Service Endpoints
All integrations endpoints are available under `/api/integrations`:

#### Connections
- `GET /api/integrations/connections` - List connections
- `GET /api/integrations/connections/{id}` - Get connection
- `POST /api/integrations/connections` - Create connection
- `PATCH /api/integrations/connections/{id}` - Update connection
- `DELETE /api/integrations/connections/{id}` - Delete connection
- `POST /api/integrations/connections/{id}/test` - Test connection
- `POST /api/integrations/connections/{id}/refresh` - Refresh connection

#### Messages
- `GET /api/integrations/messages` - List messages
- `GET /api/integrations/messages/{id}` - Get message
- `POST /api/integrations/messages` - Create message
- `PATCH /api/integrations/messages/{id}` - Update message
- `DELETE /api/integrations/messages/{id}` - Delete message
- `DELETE /api/integrations/messages?message_ids=...` - Bulk delete

#### Syncs
- `GET /api/integrations/syncs` - List syncs
- `GET /api/integrations/syncs/{id}` - Get sync
- `GET /api/integrations/syncs/{id}/status` - Get sync status
- `POST /api/integrations/syncs` - Create sync
- `PATCH /api/integrations/syncs/{id}` - Update sync
- `DELETE /api/integrations/syncs/{id}` - Delete sync

### Actions Service Endpoints
All actions endpoints are available under `/api/actions`:

#### Tasks
- `GET /api/actions/tasks?user_id={id}` - List tasks
- `GET /api/actions/tasks/{id}` - Get task
- `POST /api/actions/tasks` - Create task
- `PUT /api/actions/tasks/{id}` - Update task
- `DELETE /api/actions/tasks/{id}` - Delete task
- `POST /api/actions/tasks/batch?user_id={id}` - Create tasks from messages

#### Todos (Not Implemented)
- `GET /api/actions/todo` - List todos
- `GET /api/actions/todo/{id}` - Get todo
- `POST /api/actions/todo` - Create todo
- `PUT /api/actions/todo/{id}` - Update todo
- `DELETE /api/actions/todo/{id}` - Delete todo

#### Followups (Not Implemented)
- `GET /api/actions/followup` - List followups
- `GET /api/actions/followup/{id}` - Get followup
- `POST /api/actions/followup` - Create followup
- `PUT /api/actions/followup/{id}` - Update followup
- `DELETE /api/actions/followup/{id}` - Delete followup

### Classification Service Endpoints
All classification endpoints are available under `/api/classification`:

#### Messages
- `GET /api/classification/messages` - List messages
- `GET /api/classification/messages/{id}` - Get message
- `POST /api/classification/messages` - Create message

#### Classifications
- `GET /api/classification/classifications` - List classifications
- `GET /api/classification/classifications/{id}` - Get classification
- `POST /api/classification/classifications` - Classify messages
- `PUT /api/classification/classifications/{id}` - Update classification
- `DELETE /api/classification/classifications/{id}` - Delete classification

#### Briefs
- `GET /api/classification/briefs` - List briefs
- `GET /api/classification/briefs/{id}` - Get brief
- `POST /api/classification/briefs` - Create brief
- `DELETE /api/classification/briefs/{id}` - Delete brief

#### Tasks
- `GET /api/classification/tasks` - List tasks
- `GET /api/classification/tasks/{id}` - Get task
- `POST /api/classification/tasks` - Create task
- `PUT /api/classification/tasks/{id}` - Update task
- `DELETE /api/classification/tasks/{id}` - Delete task
- `POST /api/classification/tasks/generate` - Generate tasks from classifications

## Project Structure

```
composite-ms1/
├── main.py                 # FastAPI application entry point
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration and environment variables
├── routers/
│   ├── __init__.py
│   ├── integrations.py    # Integrations service router
│   ├── actions.py         # Actions service router
│   └── classification.py  # Classification service router
├── utils/
│   ├── __init__.py
│   ├── service_client.py  # HTTP client for atomic services
│   ├── parallel_executor.py  # Parallel execution utilities
│   ├── foreign_key_validator.py  # Foreign key validation
│   ├── db_coordinator.py  # Database connectivity coordination
│   └── logging_config.py  # Logging configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Error Handling

The composite service handles errors from atomic services:
- **502 Bad Gateway**: Service unavailable or communication error
- **504 Gateway Timeout**: Service request timeout
- **404 Not Found**: Resource not found in atomic service
- **400 Bad Request**: Invalid request to atomic service

All errors are logged with service name and request details.

## Development

### Adding New Endpoints

1. Add endpoint to appropriate router in `routers/`
2. Use `service_client` to delegate to atomic service
3. Add foreign key validation if needed using `ForeignKeyValidator`
4. Update this README with new endpoint documentation

### Testing

Ensure all atomic services are running before testing the composite service:

```bash
# Terminal 1: Integrations service
cd integrations-svc-ms2 && python main.py

# Terminal 2: Actions service
cd ms3 && python main.py

# Terminal 3: Classification service
cd ms4-classification && python main.py

# Terminal 4: Composite service
cd composite-ms1 && python main.py
```

## License

Part of the unified inbox project.

