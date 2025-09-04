# Contributing to MDUS (Multi-Document Understanding System)

Thank you for your interest in contributing to MDUS! This document provides guidelines and information for contributors.

## 🌟 Ways to Contribute

- **🐛 Bug Reports**: Help us identify and fix issues
- **💡 Feature Requests**: Suggest new features or improvements
- **🔧 Code Contributions**: Submit bug fixes or new features
- **📚 Documentation**: Improve documentation and examples
- **🧪 Testing**: Add test cases and improve test coverage
- **🎨 UI/UX**: Enhance user interface and experience

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/MDUS-system.git
cd MDUS-system

# Add upstream remote
git remote add upstream https://github.com/MichaelEnny/MDUS-system.git
```

### 2. Development Environment Setup

```bash
# Copy environment configuration
cp .env.example .env
# Edit .env with your settings

# Start development environment
docker-compose up -d

# Or set up locally
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r api-backend/requirements.txt
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-number
```

## 📋 Development Guidelines

### Code Style

#### Python (Backend)
- Follow **PEP 8** style guidelines
- Use **Black** for code formatting
- Use **isort** for import sorting
- Maximum line length: 88 characters

```bash
# Format code
black .
isort .

# Check style
flake8 .
```

#### TypeScript (Frontend)
- Follow **ESLint** configuration
- Use **Prettier** for formatting
- Use **camelCase** for variables and functions
- Use **PascalCase** for components

```bash
# Format code
npm run format

# Check style
npm run lint
```

#### SQL
- Use lowercase for keywords
- Use snake_case for table and column names
- Include appropriate indexes
- Document complex queries

### Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**
```
feat(api): add document batch processing endpoint

fix(frontend): resolve file upload timeout issue

docs(readme): update installation instructions

test(integration): add performance benchmarking tests
```

## 🧪 Testing Requirements

### Before Submitting

1. **Run All Tests**:
```bash
# Integration tests
python run_integration_tests.py

# Unit tests (when available)
pytest tests/unit/

# Frontend tests
cd web-frontend && npm test
```

2. **Code Coverage**:
   - Maintain or improve existing coverage
   - Add tests for new features
   - Include edge cases

3. **Performance Tests**:
   - Run performance benchmarks
   - Ensure no regression in response times
   - Statistical validation for performance claims

### Test Categories

#### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution (< 1s per test)

#### Integration Tests
- Test service interactions
- Use real database/cache
- Include statistical validation

#### End-to-End Tests
- Test complete workflows
- User-facing scenarios
- Performance validation

## 📝 Documentation Standards

### Code Documentation

#### Python (Docstrings)
```python
def process_document(document_id: str, options: Dict[str, Any]) -> ProcessingResult:
    """
    Process a document using AI models.
    
    Args:
        document_id: Unique identifier for the document
        options: Processing configuration options
    
    Returns:
        ProcessingResult: Results of document analysis
    
    Raises:
        DocumentNotFoundError: If document doesn't exist
        ProcessingError: If processing fails
    """
```

#### TypeScript (JSDoc)
```typescript
/**
 * Upload a document file to the server
 * @param file - The file to upload
 * @param options - Upload configuration options
 * @returns Promise that resolves to upload result
 */
async function uploadDocument(file: File, options: UploadOptions): Promise<UploadResult>
```

### API Documentation

- Update OpenAPI/Swagger specs
- Include request/response examples
- Document error codes
- Provide usage examples

### README Updates

- Update feature lists
- Add configuration options
- Include troubleshooting steps
- Update performance benchmarks

## 🔍 Code Review Process

### Before Requesting Review

1. **Self Review**:
   - Review your own code thoroughly
   - Check for potential issues
   - Ensure tests pass

2. **Documentation**:
   - Update relevant documentation
   - Add inline comments for complex logic
   - Update API documentation

3. **Testing**:
   - Add appropriate tests
   - Verify all existing tests pass
   - Include performance validation

### Review Criteria

Reviewers will check for:

- **Functionality**: Code works as intended
- **Performance**: No significant performance regression
- **Security**: No security vulnerabilities
- **Maintainability**: Code is readable and maintainable
- **Testing**: Adequate test coverage
- **Documentation**: Proper documentation updates

### Addressing Review Comments

- Respond to all review comments
- Make requested changes promptly
- Ask for clarification when needed
- Update tests based on feedback

## 🐛 Bug Reports

### Before Reporting

1. **Search Existing Issues**: Check if bug already reported
2. **Reproduce**: Ensure bug is reproducible
3. **Minimal Example**: Create minimal reproduction case

### Bug Report Template

```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: [e.g. Windows 10, macOS 12.0, Ubuntu 20.04]
- Docker Version: [e.g. 20.10.12]
- Browser: [e.g. Chrome 96.0, Firefox 95.0]
- MDUS Version: [e.g. 1.0.0]

## Additional Context
Screenshots, logs, or other relevant information
```

## 💡 Feature Requests

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature

## Problem Statement
What problem does this solve?

## Proposed Solution
Detailed description of your proposed solution

## Alternatives Considered
Other solutions you've considered

## Additional Context
Mockups, examples, or other context
```

## 🔒 Security Considerations

### Security Review

All contributions undergo security review:

- **Input Validation**: All inputs properly validated
- **Authentication**: Proper authentication checks
- **Authorization**: Appropriate access controls
- **Data Handling**: Secure data processing
- **Dependencies**: No vulnerable dependencies

### Reporting Security Issues

**Do not report security vulnerabilities through public issues.**

Instead:
1. Email security concerns to: security@mdus-system.com
2. Include detailed description
3. Provide steps to reproduce
4. Allow time for investigation before public disclosure

## 📈 Performance Guidelines

### Performance Standards

- **API Response Time**: < 200ms average
- **Database Queries**: < 50ms average
- **Cache Operations**: < 10ms
- **Memory Usage**: Monitor for leaks
- **CPU Usage**: Optimize for efficiency

### Performance Testing

```bash
# Run performance benchmarks
cd tests/integration
pytest -m performance

# Check specific metrics
pytest -m performance --benchmark-only
```

### Performance Optimization

- Profile code before optimizing
- Use appropriate data structures
- Implement efficient algorithms
- Cache frequently accessed data
- Optimize database queries

## 🎯 Acceptance Criteria

### Pull Request Checklist

- [ ] **Tests**: All tests pass
- [ ] **Code Style**: Follows project conventions
- [ ] **Documentation**: Updated where necessary
- [ ] **Performance**: No significant regression
- [ ] **Security**: Security review completed
- [ ] **Compatibility**: Backward compatibility maintained

### Definition of Done

A contribution is considered complete when:

1. **Functionality**: Feature works as specified
2. **Testing**: Adequate test coverage
3. **Documentation**: Updated documentation
4. **Review**: Code review approved
5. **CI/CD**: All automated checks pass
6. **Performance**: Performance benchmarks met

## 🤝 Community Guidelines

### Code of Conduct

- **Be Respectful**: Treat all community members with respect
- **Be Constructive**: Provide helpful and constructive feedback
- **Be Collaborative**: Work together towards common goals
- **Be Patient**: Help newcomers learn and contribute

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Requests**: Code contributions and reviews
- **Email**: Security issues and private concerns

## 🏆 Recognition

Contributors are recognized in several ways:

- **Contributors File**: Listed in CONTRIBUTORS.md
- **Release Notes**: Mentioned in release announcements
- **GitHub Recognition**: GitHub contributor statistics
- **Community Recognition**: Featured in community updates

## 📚 Additional Resources

### Learning Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://reactjs.org/docs/
- **Docker Documentation**: https://docs.docker.com/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

### Development Tools

- **VS Code Extensions**: Python, TypeScript, Docker
- **Git Hooks**: Pre-commit hooks for code quality
- **Testing Tools**: pytest, Jest, Cypress
- **Monitoring Tools**: Docker stats, performance profilers

### Project Resources

- **GitHub Repository**: https://github.com/MichaelEnny/MDUS-system
- **Issue Tracker**: https://github.com/MichaelEnny/MDUS-system/issues
- **Discussions**: https://github.com/MichaelEnny/MDUS-system/discussions
- **Wiki**: https://github.com/MichaelEnny/MDUS-system/wiki

---

Thank you for contributing to MDUS! Your contributions help make this project better for everyone. 🚀