# Contributing to Fraud Detection System

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all backgrounds and experience levels.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/fraud-detection-ml.git
   cd fraud-detection-ml
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/Nostradam4ik/fraud-detection-ml.git
   ```

## Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install black isort flake8 mypy pytest-cov

# Run the API
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend build
cd frontend
npm run build
```

## Coding Standards

### Python (Backend)

We follow PEP 8 with the following tools:

- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black app/
isort app/

# Check linting
flake8 app/

# Type checking
mypy app/ --ignore-missing-imports
```

#### Style Guidelines

```python
# Use type hints
def calculate_fraud_score(transaction: dict) -> float:
    ...

# Use docstrings for public functions
def predict_fraud(data: TransactionData) -> PredictionResult:
    """
    Predict fraud probability for a transaction.

    Args:
        data: Transaction data with all features

    Returns:
        PredictionResult with fraud probability and confidence
    """
    ...

# Constants in UPPER_CASE
MAX_BATCH_SIZE = 1000
DEFAULT_THRESHOLD = 0.5

# Classes in PascalCase
class FraudDetector:
    ...

# Functions and variables in snake_case
def get_feature_importance():
    feature_scores = {}
    ...
```

### JavaScript/React (Frontend)

- Use **ESLint** with the project configuration
- Use **Prettier** for formatting
- Prefer functional components with hooks

```javascript
// Use functional components
const TransactionForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({});

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* ... */}
    </form>
  );
};

// Use destructuring
const { data, error, isLoading } = useQuery('predictions');

// Use meaningful variable names
const fraudProbability = prediction.fraud_probability;
const isHighRisk = fraudProbability > 0.7;
```

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(auth): add two-factor authentication support

fix(predict): handle edge case for zero-amount transactions

docs(api): update endpoint documentation for batch predictions

test(auth): add unit tests for password validation
```

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Write/update tests** for your changes

4. **Run all tests** to ensure nothing is broken:
   ```bash
   cd backend && pytest tests/ -v
   cd frontend && npm run build
   ```

5. **Commit your changes** with a descriptive message

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub with:
   - Clear description of the changes
   - Reference to related issues (if any)
   - Screenshots for UI changes
   - Test results

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Tests pass locally
- [ ] New code is covered by tests
- [ ] Documentation is updated (if needed)
- [ ] No security vulnerabilities introduced
- [ ] No breaking changes (or clearly documented)

## Testing

### Backend Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_login_success -v
```

### Writing Tests

```python
# tests/test_example.py

def test_prediction_returns_valid_response(client, auth_headers, sample_transaction):
    """Test that prediction endpoint returns valid response"""
    response = client.post(
        "/api/v1/predict",
        json=sample_transaction,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "is_fraud" in data
    assert "fraud_probability" in data
    assert 0 <= data["fraud_probability"] <= 1
```

### Test Coverage

We aim for **70%+ code coverage**. The CI pipeline will fail if coverage drops below this threshold.

## Documentation

### API Documentation

- API docs are auto-generated from code using FastAPI's OpenAPI support
- Access at `/docs` (Swagger UI) or `/redoc` (ReDoc)
- Add docstrings to all endpoints:

```python
@router.post("/predict")
async def predict(
    transaction: TransactionData,
    db: Session = Depends(get_db)
) -> PredictionResponse:
    """
    Predict fraud probability for a transaction.

    - **transaction**: Transaction data with all 30 features
    - **Returns**: Prediction result with fraud probability
    """
    ...
```

### Code Documentation

- Add docstrings to all public functions and classes
- Use inline comments for complex logic
- Keep README.md updated with new features

## Questions?

If you have questions, feel free to:

1. Open an issue on GitHub
2. Check existing issues and discussions
3. Contact the maintainer via LinkedIn

---

**Thank you for contributing!** 🎉
