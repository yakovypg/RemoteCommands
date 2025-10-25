# Executor Application

The **Executor** application is used to execute commands from **Admin**.

## Quick Start

First, set the correct client ID and server URL in the `config.json` file. The client ID must match the ID in the **Admin** configuration. You can also change other properties, although it is optional. Next, follow the following steps.

## Step 1: Copy Executor

Copy the `Executor` folder to the client's `Documents` directory and open that folder.

## Step 2: Configure Executor

Configure **Executor** with `configure.bat` (on Windows) or `configure.sh` (on Linux/Mac) script.

```
configure.bat
```

## Step 3: Check Autostart Scripts

Check the `run-executor.bat` and `run-executor.vbs` scripts. If you saved the `Executor` folder somewhere other than `Documents`, update the paths accordingly.

## Step 4: Configure Autostart

Currently, autostart configuration instructions are available only for Windows.

You can configure autostart using the `add-autostart-task-highest.bat` or `add-autostart-task-limited.bat` script. The first adds a task with highest privileges; the second adds a task with limited privileges. Please note that if you saved the `Executor` folder somewhere other than `Documents`, update the paths in these scripts accordingly.

Alternatively, you can configure autostart manually using the steps described below.

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

Reboot the computer and verify that `executor.py` is running. It's possible that the first time the autorun script is launched you'll be prompted to confirm it. In this case you should confirm the prompt and uncheck the option that asks to confirm every time. You can confirm this in Task Manager &mdash; the process should be `python.exe`.