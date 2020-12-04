# Lifelong Learning Logger Examples

In this folder, there are two examples for demonstrating effective usage of
the logger. Additionally in this folder, there are example `logger_info.json`
and `scenario_info.json` files that were produced from a run of `mock_simple_workflow`:

- [example_logger_info.json](example_logger_info.json)
- [example_scenario_info.json](example_scenario_info.json)

## mock_simple_workflow

Demonstrates a very simple mock RL workflow which would utilize the logger
library. Consists of three files:

- `driver.py`:
  - The main script for the example; creates the logger object and
    contains all interfacing calls with it.
- `mock_agent.py`:
  - A helper file to manage the RL "magic" side of things, e.g. parsing
  an example scenario input file, managing the `block_num` and `exp_num`
  sequences as it goes.
  - Contains excessively simple `Experience` class representing an RL task;
  upon invocation, just returns hardcoded 'reward' and 'debug_info' columns.
- `simple_scenario.json`
  - An invented format for representing a learning/testing scenario; also
  contains the top level dir (*relative to current working directory*), in
  which the scenario directory will be made.
  - Note that this format is not special in any way; it is just convenient
  for the example to show the API of the logger.
  Clients can use whatever scheme fits their codebase best in order to
  generate the sequences of blocks and experiences. For instance, the
  example uses the term `regime` to refer to groups of experiences within
  a single block that have the same `task_name` and `task_params`.
    - This is true for the parallel example below as well.

Ensure the virtual environment is active, then run simply via:

```bash
cd mock_simple_workflow
python driver.py
```

This will create logs in whichever relative folder is specified in the
`logging_base_dir` entry within `simple_scenario.json`.

Repeated invocations will create their own scenario folders, with the
timestamp included as part of the name, as suggested.

## mock_parallel_workflow

Demonstrates usage of multiprocessing with the logging library.
In this example, the logging and agent aspects of the program are mostly
handled together in the `LoggerInfo` class within `parallel_helper.py`, while
`parallel_example.py` focuses on enabling the parallel aspects of the script.
For this reason, please ensure you're first familiar with the simple example.

This example also demonstrates the usefulness of each worker having
its own folder within the scenario directory, to simplify synchronization as
each process gets its own copy of the logger instance.

Ensure the virtual environment is active, then run simply via:

```bash
cd mock_parallel_workflow
python parallel_example.py input_parallel.json
```

This will create logs in whichever relative folder is specified in the
`logging_base` field within `input_parallel.json`

You can specify the number of workers/processes via changing the `threads`
field within `input_parallel.json` as well.

## Tips

- Make sure to not add logs produced from the examples to git.
- On certain Windows environments, the `mock_parallel_workflow` example may
  produce an error or inconsistent output; for this reason, we highly suggest
  using Ubuntu 18 or macOS for experimenting with the parallel example.
