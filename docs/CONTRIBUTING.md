# Contributing Guidelines

Thank you for your interest in contributing to the Article Summarizer Telegram Bot! We welcome contributions of all kinds, from bug reports to feature enhancements.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on our GitHub repository. Make sure to include:
- A clear and descriptive title.
- A detailed description of the bug and the steps to reproduce it.
- Your environment details (e.g., Python version, OS).
- Any relevant logs or screenshots.

### Suggesting Enhancements

If you have an idea for a new feature or an improvement to an existing one, please open an issue to discuss it. This allows us to coordinate efforts and ensure the proposed change aligns with the project's goals.

### Submitting Code Changes

1.  **Fork the Repository:**
    Create your own fork of the project on GitHub.

2.  **Create a Branch:**
    Create a new branch for your changes from the `main` branch.
    ```bash
    git checkout -b feature/your-feature-name
    ```

3.  **Make Your Changes:**
    Write your code and make sure to follow the existing code style.

4.  **Test Your Changes:**
    Ensure that your changes do not break any existing functionality. If you are adding a new feature, please add tests for it.

5.  **Commit Your Changes:**
    Write a clear and concise commit message.
    ```bash
    git commit -m "feat: Add a new summarization prompt"
    ```

6.  **Push to Your Fork:**
    ```bash
    git push origin feature/your-feature-name
    ```

7.  **Create a Pull Request:**
    Open a pull request from your fork to the main repository. Provide a detailed description of your changes in the PR description.

## Development Setup

Follow the instructions in the [INSTALLATION.md](INSTALLATION.md) guide to set up your local development environment.

## Code Style

This project follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. We use `black` for code formatting and `flake8` for linting. Before submitting your changes, please run these tools to ensure your code is compliant.

```bash
pip install black flake8
black .
flake8 src
```

Thank you for contributing!
