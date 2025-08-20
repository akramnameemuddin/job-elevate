# Contributing to Job Elevate

Thank you for your interest in contributing to Job Elevate! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information** including:
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Screenshots (if applicable)
   - Environment details (OS, Python version, etc.)

### Suggesting Features

1. **Check the roadmap** to see if the feature is already planned
2. **Open a feature request** with detailed description
3. **Explain the use case** and why it would be valuable
4. **Consider implementation complexity** and provide suggestions

### Code Contributions

#### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/job-elevate.git
   cd job-elevate
   ```
3. **Set up the development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Development Guidelines

##### Code Style
- Follow **PEP 8** for Python code
- Use **meaningful variable and function names**
- Add **docstrings** for all functions and classes
- Keep **line length under 88 characters** (Black formatter standard)
- Use **type hints** where appropriate

##### Django Best Practices
- Follow **Django coding style** guidelines
- Use **class-based views** where appropriate
- Implement **proper error handling**
- Add **appropriate logging**
- Use **Django's built-in features** (forms, admin, etc.)

##### Frontend Guidelines
- Write **semantic HTML**
- Use **CSS classes** consistently
- Ensure **responsive design**
- Test across **different browsers**
- Follow **accessibility guidelines**

#### Testing

1. **Write tests** for new features and bug fixes
2. **Run the test suite** before submitting:
   ```bash
   python manage.py test
   ```
3. **Ensure code coverage** doesn't decrease
4. **Test manually** in the browser

#### Database Changes

1. **Create migrations** for model changes:
   ```bash
   python manage.py makemigrations
   ```
2. **Test migrations** both forward and backward
3. **Include migration files** in your commit

#### Commit Guidelines

1. **Use clear commit messages**:
   ```
   feat: add job recommendation algorithm
   fix: resolve login redirect issue
   docs: update installation instructions
   style: format code with black
   refactor: simplify user profile logic
   test: add tests for job search functionality
   ```

2. **Keep commits focused** - one logical change per commit
3. **Reference issues** in commit messages when applicable

#### Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** with your changes
5. **Create a pull request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots (for UI changes)
   - Testing instructions

## 🏗️ Development Setup

### Prerequisites
- Python 3.8+
- Git
- Virtual environment tool

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example backend/backend/.env
   # Edit the .env file with your settings
   ```

3. **Run migrations**:
   ```bash
   cd backend
   python manage.py migrate
   ```

4. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Start development server**:
   ```bash
   python manage.py runserver
   ```

### Code Quality Tools

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **pytest**: Testing

Run all quality checks:
```bash
black .
isort .
flake8 .
pytest
```

## 📋 Project Structure

```
job-elevate/
├── backend/                 # Django application
│   ├── accounts/           # User management
│   ├── jobs/              # Job functionality
│   ├── resume_builder/    # Resume creation
│   ├── community/         # Community features
│   ├── dashboard/         # User dashboards
│   ├── learning/          # Learning modules
│   ├── assessments/       # Skill assessments
│   ├── recruiter/         # Recruiter tools
│   └── backend/           # Project settings
├── static/                # Static files
├── media/                 # User uploads
└── docs/                  # Documentation
```

## 🎯 Areas for Contribution

We welcome contributions in these areas:

- **Bug fixes** and performance improvements
- **New features** and enhancements
- **Documentation** improvements
- **Test coverage** expansion
- **UI/UX** improvements
- **Accessibility** enhancements
- **Internationalization** (i18n)
- **API** development and documentation

## 📞 Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Email**: For security issues or private matters

## 🏆 Recognition

Contributors will be recognized in:
- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **GitHub contributors** section

Thank you for contributing to Job Elevate! 🚀
