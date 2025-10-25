# Admin Application

The **Server** application is used to provide communications between **Admin** and **Executor**.

## Quick Start

First, you can change configuration in `config.json`, although it is optional.

Next, follow these steps:

1. Build Docker container.
    ```bash
    docker compose -f docker-compose.yml build
    ```
2. Run the server in Docker
    ```bash
    docker compose -f docker-compose.yml up -d
    ```

You can also start the server without Docker. To do this, follow these steps:
1. Create virtual environment.
    ```bash
    python -m venv .venv
    ```
2. Activate virtual environment (on Linux).
    ```bash
    source .venv/bin/activate
    ```

    If you are using Windows, you can do the same with the following command.

    ```bat
    call .venv\Scripts\activate
    ```

3. Install necessary packages.
    ```bash
    pip install -r requirements.txt
    ```

4. Run the application
    ```bash
    python server.py
    ```