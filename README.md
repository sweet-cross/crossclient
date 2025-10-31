# crossclient
Python client to interact with the SWEET-CROSS API

## Development

### Process
To contribute to development, create an issue to start a discussion about new features,
enhancements, and bugs. Assign the feature to yourself and create a branch related
to the issue. Create the development setup as described belows. Once you're done,
create a pull request to merge the new code into the main branch.

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd cross_back
```

2. Install dependencies:
```bash
uv sync --all-groups
```

This will install all dependencies including dev and docs dependencies.

### Pre-commit hooks

We use pre-commit hooks to check and format the code before committing. Once you
installed the dependencies run
```bash
pre-commit install
```