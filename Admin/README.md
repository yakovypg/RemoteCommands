# Admin Application

The **Admin** application is used to send commands to **Executor**.

## Quick Start

First, set the correct client ID and server URL in the `config.json` file. The client ID must match the ID in the **Executor** configuration. You can also change other properties, although it is optional.

Next, follow these steps:

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
    python admin.py
    ```