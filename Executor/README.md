# Executor Application

The **Executor** application is used to execute commands from **Admin**.

## Quick Start

First, set the correct client ID and server URL in the `config.json` file. The client ID must match the ID in the **Admin** configuration. You can also change other properties, although it is optional. Next, follow the following steps.

## Step 1: Copy Executor

Copy the `Executor` folder to the client's `Documents` directory and open that folder.

## Step 2: Create Virtual Environment

Create a virtual environment for **Executor**.

```bash
python -m venv .venv
```

## Step 3: Create Autostart Scripts

Create `run-executor.bat` and `run-executor.vbs` from the templates `run-executor-template.bat` and `run-executor-template.vbs`. Replace `__USER__` with the client user name.

## Step 4: Configure Autostart

Currently, autostart configuration instructions are available only for Windows.

### Open Task Scheduler

Win &rarr; Run &rarr; taskschd.msc

### Create Task

In the right pane, click `Create Task`.

#### Configure `General` Tab

Change the following fields:
- **Name:** RunExecutor
- Check the box to run with highest privileges
- **Configure for:** select the client's Windows version

#### Configure `Triggers` Tab

Change the following fields:
- **Start task:** at log on

#### Configure `Actions` Tab

Change the following fields:
- **Action:** start a program
- **Script:** C:\Windows\System32\wscript.exe
- **Arguments:** "C:\Users\\_\_USER\_\_\Documents\Executor\run-executor.vbs"
- **Start in:** C:\Users\\_\_USER\_\_\Documents\Executor

Remember to replace `__USER__` with the client user name. Note that the `Arguments` value must be enclosed in quotes.

#### Configure `Conditions` Tab

Uncheck any boxes that might prevent autostart. For example, "Start the task only if the computer is on AC power".

## Step 5: Check Process

Reboot the computer and verify that `executor.py` is running. You can confirm this in Task Manager &mdash; the process should be `python.exe`.