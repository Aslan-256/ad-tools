# start_sploit.py report

This document describes what each function and method in [start_sploit.py](start_sploit.py) does.

## Overview

`start_sploit.py` is a farm client runner. It launches a sploit against targets, captures stdout, extracts flags from output, queues them for submission, and periodically posts them to the farm API.

## Top-level functions

| Function | Purpose |
|---|---|
| `highlight` | Adds ANSI styling to text on non-Windows systems so logs and banners are easier to read. |
| `parse_args` | Defines the command-line interface and parses options such as the sploit path, server URL, token, concurrency, and attack mode. |
| `fix_args` | Normalizes parsed arguments, validates the sploit file, ensures the server URL has a scheme, and parses `--distribute`. |
| `check_script_source` | Performs lightweight checks on script-based sploits, mainly shebang presence and flush behavior for reliable flag output. |
| `check_sploit` | Verifies the sploit file exists and is runnable, auto-selects an interpreter on Windows for scripts, and ensures executable permissions on Unix-like systems. |
| `get_config` | Requests the farm configuration from `/api/get_config` and decodes the JSON response. |
| `post_flags` | Sends collected flags to `/api/post_flags` in the format expected by the farm server. |
| `once_in_a_period` | Produces iteration numbers at a fixed interval and stops when shutdown is requested. |
| `run_post_loop` | Background loop that repeatedly posts queued flags and logs success or retry conditions. |
| `display_sploit_output` | Prints a team’s sploit output in a readable grouped block, protected by a lock to avoid interleaving. |
| `process_sploit_output` | Reads a sploit’s output stream, extracts flags using the configured regex, stores them, and optionally logs the captured text. |
| `launch_sploit` | Builds the subprocess command for a target, starts the sploit, starts output processing, and registers the running instance. |
| `run_sploit` | Controls the full lifecycle of a single sploit execution, including timeout handling, process cleanup, and statistics updates. |
| `show_time_limit_info` | Logs the effective time budget per sploit and warns when the attack period is likely too long for the server timing. |
| `_extract_team_addr` | Looks for a usable target address in a team object under common field names such as `addr`, `ip`, `host`, or `target`. |
| `normalize_teams` | Converts server team configuration into a uniform team-name-to-address mapping, supporting both dict and list input shapes. |
| `get_target_teams` | Applies per-team selection rules, distribution filtering, and warning messages before launching attacks. |
| `main` | Coordinates the whole client: validates arguments, starts background posting, fetches config, computes time limits, and schedules attacks. |
| `shutdown` | Signals all background loops to stop and kills tracked child processes. |

## Windows-specific helpers

| Function | Purpose |
|---|---|
| `_errcheck_bool` | ctypes error checker for WinAPI calls; raises a Windows error if the API indicates failure. |
| `win_ctrl_handler` | Custom Ctrl+C handler for Windows so the client can stop itself cleanly instead of leaving subprocesses in control. |

## Class methods

### `FlagStorage`

| Method | Purpose |
|---|---|
| `__init__` | Creates the deduplication set, pending queue, and lock used to protect them. |
| `add` | Adds new flags to the queue only once and records the associated team name. |
| `pick_flags` | Returns a copy of the current queue contents for posting. |
| `mark_as_sent` | Removes the first `N` queued flags after a successful submission. |
| `queue_size` | Returns the current queue length in a thread-safe way. |

### `InstanceStorage`

| Method | Purpose |
|---|---|
| `__init__` | Initializes the instance registry and counters for completed and killed processes. |
| `register_start` | Stores a newly launched process under a unique instance ID and returns that ID. |
| `register_stop` | Removes a finished instance and updates completion/timeout counters. |

## Entrypoint behavior

When run directly, the script calls `main(parse_args())`, logs `KeyboardInterrupt` cleanly, and always runs `shutdown()` in a `finally` block.

## Practical flow

1. Parse and validate CLI arguments.
2. Fetch the farm config.
3. Normalize team targets.
4. Launch one sploit process per target.
5. Read stdout, extract flags, and queue them.
6. Post queued flags on a background timer.
7. Stop and clean up on exit.