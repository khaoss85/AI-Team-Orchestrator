# Tests Directory

## Structure

- **unit/**: Unit tests for individual components
- **integration/**: Integration tests for multiple components working together
- **e2e/**: End-to-end tests for complete workflows
- **fixtures/**: Test data and fixtures

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test type
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest tests/ --cov=backend
```

## Guidelines

- Keep tests isolated and independent
- Use fixtures for common test data
- Follow naming convention: test_*.py
- Include docstrings for complex test scenarios