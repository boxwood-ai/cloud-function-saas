# Contributing to Cloud Function SaaS Generator

We love your input! We want to make contributing to this project as easy and transparent as possible.

## 🚀 Quick Start for Contributors

1. **Fork the repo and clone it locally**
   ```bash
   git clone https://github.com/yourusername/cloud-function-saas.git
   cd cloud-function-saas
   ```

2. **Set up development environment**
   ```bash
   ./scripts/setup.sh
   source venv/bin/activate
   pip install -r requirements/dev.txt
   ```

3. **Run tests to ensure everything works**
   ```bash
   ./scripts/test.sh
   ```

## 🛠️ Development Workflow

### Making Changes
1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Add tests for new functionality
4. Run the full test suite: `pytest`
5. Run linting: `./scripts/lint.sh`
6. Update documentation if needed

### Commit Guidelines
We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation changes
- `test:` adding tests
- `refactor:` code refactoring
- `security:` security improvements

Example: `feat: add AWS Lambda support`

### Pull Request Process
1. Ensure all tests pass
2. Update README.md if needed
3. Add examples for new features
4. Link any relevant issues
5. Request review from maintainers

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_generator.py

# Run with coverage
pytest --cov=src

# Run integration tests
pytest tests/integration/
```

### Adding Tests
- Unit tests go in `tests/unit/`
- Integration tests go in `tests/integration/`
- Use fixtures in `tests/fixtures/`
- Mock external services (Claude API, gcloud CLI)

## 🏗️ Architecture Guidelines

### Code Organization
- Keep functions small and focused
- Use type hints throughout
- Follow PEP 8 style guidelines
- Add docstrings to all public functions
- Separate concerns (parsing, generation, deployment)

### Security Guidelines
- Never commit secrets or API keys
- Sanitize all inputs and outputs
- Use parameterized subprocess calls
- Validate file paths to prevent traversal
- Follow principle of least privilege

### Performance Considerations
- Cache AI responses when possible
- Use async operations for I/O
- Implement retry logic with exponential backoff
- Minimize resource usage in containers

## 🎯 What We're Looking For

### High Priority
- [ ] Support for additional cloud providers (AWS, Azure)
- [ ] Better error handling and user feedback
- [ ] Template system for custom code generation
- [ ] Integration tests with actual cloud deployments
- [ ] Performance optimizations

### Medium Priority
- [ ] Web UI for spec file creation
- [ ] Database integration templates
- [ ] Monitoring and observability templates
- [ ] Multi-language support (Python, Go, etc.)

### Good First Issues
Look for issues labeled `good-first-issue` - these are perfect for new contributors!

## 📝 Documentation

### Writing Docs
- Use clear, concise language
- Include code examples
- Add screenshots where helpful
- Keep examples up to date

### API Documentation
- Document all public functions
- Include parameter types and return values
- Add usage examples
- Document error conditions

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help newcomers get started
- Provide constructive feedback
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md)

## 🐛 Reporting Issues

### Security Issues
Report security vulnerabilities privately to security@yourproject.com
See [SECURITY.md](SECURITY.md) for details.

### Bug Reports
Include:
- Steps to reproduce
- Expected vs actual behavior
- System information
- Relevant logs or error messages

### Feature Requests
- Describe the problem you're solving
- Explain why this would be useful
- Consider providing a proposed implementation

## 📞 Getting Help

- Join our Discord: [link]
- Check existing issues and discussions
- Read the documentation
- Ask questions in GitHub Discussions

Thank you for contributing! 🎉