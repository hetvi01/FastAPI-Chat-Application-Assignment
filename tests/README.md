# FastAPI Chat Application Testing

This directory contains the test suite for the FastAPI Chat Application. The tests are organized by level of abstraction and responsibility.

## Test Structure

- `tests/conftest.py`: Contains shared pytest fixtures used across all tests
- `tests/test_api/`: Contains API-level tests (endpoints and integration)
  - `test_auth.py`: Tests for authentication APIs
  - `test_chats.py`: Tests for chat management APIs
  - `test_messages.py`: Tests for message APIs
  - `test_branches.py`: Tests for branch management APIs
  - `test_integration.py`: End-to-end flow tests across multiple APIs
- `tests/test_services/`: Contains service-level tests
  - `test_chat_service.py`: Tests for Chat Service
  - `test_user_service.py`: Tests for User Service

## Running Tests

To run the entire test suite:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_api/test_auth.py
```

To run tests with coverage:

```bash
pytest --cov=app
```

## Testing Strategy

### Unit Tests

Unit tests focus on testing individual components in isolation:

- **Service Layer Tests**: Tests in `tests/test_services/` verify that service functions work correctly with mocked repositories.
- **API Layer Tests**: Tests in `tests/test_api/` verify that API endpoints handle requests and responses correctly with mocked services.

### Integration Tests

Integration tests verify that multiple components work correctly together:

- **API Integration**: Tests in `tests/test_api/test_integration.py` verify end-to-end flows across multiple API endpoints.

### Mocking Strategy

- **Database**: All database interactions are mocked to avoid requiring a real database for testing.
- **Dependencies**: FastAPI dependencies like `get_current_user` and `get_db` are overridden with test versions.
- **External Services**: Any external service calls (like AI services) are mocked.

## Adding New Tests

When adding new tests:

1. Place API tests in the appropriate file in `tests/test_api/`
2. Place service tests in the appropriate file in `tests/test_services/`
3. For new components:
   - Create a new test file following the naming convention `test_<component_name>.py`
   - Add appropriate fixtures to test your component in isolation
   - Use the existing test structure as a reference 