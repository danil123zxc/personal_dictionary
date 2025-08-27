# Personal Dictionary API Tests

This directory contains comprehensive tests for the Personal Dictionary API CRUD functions.

## Test Structure

### `test_crud.py`
Main test file containing unit tests for all CRUD functions:

- **User Functions**: Registration, login, profile management
- **Language Functions**: Language creation and management
- **Learning Profile Functions**: Profile creation and validation
- **Word Functions**: Word creation, synonym search, updates
- **Dictionary Functions**: Dictionary entry management
- **Translation Functions**: Translation creation and updates
- **Example Functions**: Example sentence management
- **Definition Functions**: Definition management
- **Text Functions**: Text creation and management

### `conftest.py`
Shared pytest fixtures for:
- Mock database sessions
- Sample data objects
- Authentication headers
- Mock embedding responses

## Running Tests

### Install Test Dependencies
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# CRUD tests only
pytest -m crud

# Vector similarity tests
pytest -m vector

# Authentication tests
pytest -m auth
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/test_crud.py
```

### Run Specific Test Function
```bash
pytest tests/test_crud.py::TestUserFunctions::test_register_user_success
```

## Test Features

### 🔒 **Security Testing**
- User authorization checks
- Access control validation
- Duplicate prevention

### ✅ **Validation Testing**
- Input validation with Pydantic models
- Error handling and HTTP exceptions
- Database constraint validation

### 🔄 **Embedding Testing**
- Mock embedding generation
- Vector similarity search
- Embedding update scenarios

### 🗄️ **Database Testing**
- Mock SQLAlchemy sessions
- Transaction testing
- Query optimization

### 🚀 **Performance Testing**
- Single query optimization
- HNSW index usage
- Efficient filtering

## Test Coverage

The tests cover:

- **Success scenarios**: Normal operation paths
- **Error scenarios**: Exception handling
- **Edge cases**: Boundary conditions
- **Security**: Authorization and access control
- **Data integrity**: Validation and constraints
- **Performance**: Query optimization

## Adding New Tests

### For New CRUD Functions:
1. Add test class in `test_crud.py`
2. Create fixtures in `conftest.py` if needed
3. Test success, error, and edge cases
4. Mock external dependencies (embeddings, auth)

### Example Test Structure:
```python
class TestNewFunction:
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    def test_success_scenario(self, mock_db):
        # Arrange
        # Act
        # Assert
    
    def test_error_scenario(self, mock_db):
        # Test error handling
```

## Continuous Integration

Tests are configured to:
- Run automatically on code changes
- Generate coverage reports
- Fail if coverage drops below 80%
- Provide detailed error reporting

## Mock Strategy

- **Database**: Mock SQLAlchemy sessions
- **Embeddings**: Mock embedding generation
- **Authentication**: Mock JWT tokens and user objects
- **External APIs**: Mock HTTP responses

This ensures fast, reliable tests that don't depend on external services.
