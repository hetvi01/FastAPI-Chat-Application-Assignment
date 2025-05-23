# FastAPI Chat Application with Branching Functionality

This application provides a microservice-based chat backend using FastAPI that allows users to create chat conversations and branch conversations from any point in the chat history.

## Features

- Create and manage chat conversations
- Add messages to existing chats
- Branch conversations from any point in chat history
- Authentication system
- Dual database approach (PostgreSQL and MongoDB)
- Caching for performance optimization

## Technical Stack

- **Framework**: FastAPI
- **Databases**:
  - PostgreSQL (with SQLModel ORM)
  - MongoDB
- **Additional Libraries**:
  - Pydantic for data validation
  - Alembic for database migrations
  - Motor for async MongoDB access
  - FastAPI-cache for caching
  - JWT for authentication

## Prerequisites

Before setting up the application, ensure you have the following installed:

1. **Docker and Docker Compose** - Required to run the containerized application
2. **Python 3.11+** - If you want to run the application locally
3. **Git** - To clone the repository

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── chats.py
│   │   │   │   ├── messages.py
│   │   │   │   └── branches.py
│   │   │   └── router.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── mongodb.py
│   │   └── postgres.py
│   ├── models/
│   │   ├── chat.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── chat.py
│   │   ├── message.py
│   │   └── user.py
│   ├── services/
│   │   ├── chat_service.py
│   │   └── message_service.py
│   ├── repositories/
│   │   ├── chat_repository.py
│   │   └── message_repository.py
│   ├── utils/
│   │   └── helpers.py
│   └── main.py
├── alembic/
│   └── ...
├── tests/
│   ├── test_api/
│   └── test_services/
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Setup and Installation

### Using Docker (Recommended)

1. Clone the repository:

```bash
git clone <repository-url>
cd fastapi-chat-application
```

2. Create and configure the .env file:

```bash
cp .env.example .env
# Edit .env with your configuration if needed
```

3. Start the application with Docker Compose:

```bash
docker-compose up -d
```

This will automatically set up:
- PostgreSQL database
- MongoDB database
- Redis for caching
- The FastAPI application

4. The API will be available at: http://localhost:8000

5. Access the API documentation at: http://localhost:8000/docs

### Manual Setup (Without Docker)

If you prefer to run the services locally:

1. Install PostgreSQL:
   - Create a database named `chat_app`
   - Create a user with appropriate permissions
   - Update the database connection info in `.env`

2. Install MongoDB:
   - Start MongoDB server
   - Create a database named `chat_content`
   - Update the MongoDB connection URL in `.env`

3. Install Redis:
   - Start the Redis server
   - Update the Redis connection info in `.env`

4. Install Python dependencies:

```bash
pip install -r requirements.txt
```

5. Run database migrations:

```bash
alembic upgrade head
```

6. Start the application:

```bash
uvicorn app.main:app --reload
```

## Database Setup Details

### PostgreSQL

The application uses PostgreSQL for storing chat metadata and user information.

- **Database**: `chat_app` # db_name
- **Tables**:
  - `users`: User account information
  - `chats`: Chat metadata
  - `conversations`: Conversation information and branching structure

When using Docker, the database is automatically created. For manual setup:

```sql
CREATE DATABASE chat_app;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE chat_app TO postgres;
```

### MongoDB

MongoDB stores the actual conversation content.

- **Database**: `chat_content`
- **Collection**: `chat_content`

Document structure:
```json
{
  "chat_id": "uuid",
  "qa_pairs": [
    {
      "question": "User question",
      "response": "AI response",
      "response_id": "unique_id",
      "timestamp": "ISO datetime",
      "branches": ["branch_chat_id1", "branch_chat_id2"]
    }
  ]
}
```

### Redis

Redis is used for caching and performance optimization.

## API Endpoints

### Chat Management
- POST /api/v1/chats/create-chat - Create a new chat
- GET /api/v1/chats/get-chat - Get chat details and messages
- PUT /api/v1/chats/update-chat - Update chat metadata
- DELETE /api/v1/chats/delete-chat - Delete a chat

### Message Management
- POST /api/v1/messages/add-message - Add a message to a chat

### Branch Management
- POST /api/v1/branches/create-branch - Create a branch from a specific message
- GET /api/v1/branches/get-branches - Get all branches for a chat
- PUT /api/v1/branches/set-active-branch - Set a specific branch as active

## Development

### Running Tests

```bash
pytest
```

### Running Migrations

```bash
alembic upgrade head
``` 