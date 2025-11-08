💖 **[Support Development](https://github.com/sponsors/notesofcliff)** - Sponsor on GitHub

# swatctl

`swatctl` is a command-line tool for managing [SWAT (Static Web App Toolkit)](../swat) projects.

It helps with common tasks like creating new projects, managing application pages, and setting the version of the core SWAT library.

## Features

- `create-project`: Scaffolds a new SWAT project with a standard directory structure.
- `create-page`: Adds a new application page to an existing project.
- `swat-set-version`: Replaces the `lib/` directory with a version from a specified git repository and tag.
- `plugin-install`: Installs a plugin from a URL.
- `plugin-set-version`: Sets the version of an installed plugin.
- `info`: Displays information about the current SWAT project.

## Installation and Usage

1.  **Install for development**:
    ```bash
    # It is recommended to clone the repository and install in editable mode
    pip install -e ".[test]"
    ```

2.  **Run tests**:
    ```bash
    pytest -q
    ```

3.  **Run the CLI**:
    To see a list of all available commands, run:
    ```bash
    swatctl --help
    ```

For a detailed workflow, see the [Development Workflow section in the main SWAT repository](../swat/README.md#development-workflow).