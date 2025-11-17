# Contributing to Universe MCP

Thank you for your interest in contributing to Universe MCP! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

### 1. Report Issues
- **Data Issues**: Found incorrect or missing data? [Open an issue](https://github.com/willabs-ia/universe_mcp/issues)
- **Bugs**: Encountered a bug in the scrapers or scripts? Report it with details
- **Feature Requests**: Have ideas for new features? Share them!

### 2. Improve Data Quality
- Submit corrections to existing server/client data
- Add missing servers or clients not yet in the database
- Enhance metadata and descriptions

### 3. Enhance Code
- Improve scraper efficiency
- Add new indexing strategies
- Fix bugs
- Add tests
- Improve documentation

### 4. Documentation
- Fix typos or unclear instructions
- Add usage examples
- Improve integration guides
- Translate documentation

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Git
- Basic understanding of web scraping (for scraper contributions)

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/universe_mcp.git
cd universe_mcp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests (if adding code)
python scripts/update.py --test
```

## 📝 Contribution Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

### Commit Messages
Use conventional commits format:
```
type(scope): description

[optional body]
[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `data`: Data updates or corrections
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(scraper): add support for scraping server tags
fix(validator): correct JSON schema validation error
docs(readme): update installation instructions
data: add 15 new community servers
```

### Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clean, documented code
   - Add tests if applicable
   - Update documentation

3. **Validate Your Changes**
   ```bash
   # If modifying scrapers
   python scripts/update.py --test

   # If adding/modifying data
   python scripts/validators/validate_data.py
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Provide a clear title and description
   - Reference any related issues
   - Explain what changes were made and why

### Data Contributions

When adding or updating server/client data:

1. **Follow the Schema**
   - Ensure data conforms to JSON schemas in `/schemas/`
   - Use `validate_data.py` to check

2. **Provide Complete Information**
   ```json
   {
     "id": "server-slug",
     "name": "Server Name",
     "provider": "Organization",
     "description": "Clear, concise description",
     "classification": "official|reference|community",
     "url": "https://pulsemcp.com/servers/...",
     "source_url": "https://github.com/..."
   }
   ```

3. **Verify Accuracy**
   - Double-check all URLs work
   - Ensure descriptions are accurate
   - Verify classification is correct

## 🧪 Testing

Before submitting:

```bash
# Test scrapers (limited run)
python scripts/scrapers/scrape_servers.py --test

# Validate all data
python scripts/validators/validate_data.py

# Generate indexes
python scripts/indexers/generate_indexes.py
```

## 🐛 Reporting Bugs

Include in your bug report:
- **Description**: Clear description of the issue
- **Steps to Reproduce**: How to trigger the bug
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, etc.
- **Logs**: Relevant error messages or logs

## 💡 Suggesting Features

For feature requests, include:
- **Use Case**: Why is this feature needed?
- **Proposal**: How should it work?
- **Alternatives**: Other solutions considered
- **Additional Context**: Screenshots, examples, etc.

## 📋 Code Review Process

1. Maintainers will review PRs within 1-2 weeks
2. Feedback will be provided for requested changes
3. Once approved, PRs will be merged
4. Contributors will be credited in release notes

## 🏆 Recognition

Contributors will be:
- Listed in project acknowledgments
- Credited in relevant commits/PRs
- Mentioned in release notes

## 📞 Questions?

- **GitHub Discussions**: For questions and discussions
- **Issues**: For bug reports and feature requests
- **Email**: For private inquiries

## 📜 Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build something great together.

---

**Thank you for contributing to Universe MCP! 🌌**
