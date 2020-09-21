# Lifelong Learning Performance Logger (L2Logger)

The Lifelong Learning Logger (L2Logger) is a library to produce logs for metrics calculation.

## Library Overview

The Performance Logger is a utility module provided for producing logs in a
convenient format for the associated l2metrics module, but can also be used
independently. At a high level, the library is used simply by creating an
instance of the logger object, then by invoking the `write_blocks_to_log`
and `write_data_to_log` member functions on it when desired.

The logger produces output according to the structure below. At
instantiation, the logger takes in `logging_base_dir` to start as the 
top-level logging directory, creating it if it doesn't exist already.

### Directory Structure
```
logging_base_dir
└───scenario_dir
    │   scenario_info.json
    │   column_metric_list.json
    │
    └───worker-0
    │   └───block-0
    │   │    └───task-0
    │   │    │    │   block-report.tsv
    │   │    │    │   data-log.tsv
    │   │    │ 
    │   │    ...
    │   │    │
    │   │    └───task-n
    │   │         │   block-report.tsv
    │   │         │   data-log.tsv
    │   ...
    │   │
    │   └───block-n
    │        └───task-0
    │        │    │   block-report.tsv
    │        │    │   data-log.tsv
    │        │ 
    │        ...
    │        │
    │        └───task-n
    │             │   block-report.tsv
    │             │   data-log.tsv
    │    
    │   
    │   
    ...   
    └───worker-n
    │   └───block-0
    │   │    ...
    │   │
    │   ...
    │   └───block-n
    │   │    ...
    │   ...
    ...
``` 

This nomenclature assumes the following hierarchical organization of tasks:

- `Scenario`: the overall sequence of `blocks`, typically alternating  
               between training and testing
- `Block`: a sequence of `regimes`, all with the same block type (i.e. train or test)
- `Regime`: a sequence of `experiences`, all with the same parameters and name
- `Experience`: a specific instance of a task (e.g. an instance of a gym
                environment of the given name, with the provided parameters)

From the directory structure, `scenario_dirname` should be the name of a 
specific run of a given scenario (e.g. the scenario name followed by a
timestamp, like `simple-1600697775-609517`).
Within this folder are `scenario_info.json` and `column_metric_list.json`:
- Scenario info is a file for any meta-data the developer wishes
to output along with the logs (e.g. 'author', or 'scenario-version'). 
- Column metric list consists of a list of which data columns metrics may
  be computed upon (e.g. 'reward').
  This is primarily used by `l2metrics` as a validation step

The interface for providing this information to the logger is explained in more detail below. 

Still within this top-level scenario directory, each
worker (e.g. thread or process) then gets its own folder to write logs to.
Within a worker's folder, there is a folder for each block in the syllabus
that the worker consumed experiences on (e.g. '0-train', '1-test', etc). 
Within these block directories, there are then folders for each different task
that these consumed experiences entailed (e.g. 'Env-A-5x5', 'Env-B-2x2', etc.).
Finally within these task folders are the actual TSV log files: 
`block-report.tsv` and `data-log.tsv`. The exact content of these are explained
below as well.

## Interface

### Initialization

The logger is instantiated by creating an instance of one of two sub-classes
of PerformanceLogger:
- RLPerformanceLogger
- ClassifPerformanceLogger

These differ only in the base columns required when writing to the data log.
The logger takes three input arguments:
- `toplevel_dir`: this is the `logging_base_dir` as described above
- `column_list` (default: `[]`): the list of metric-computable columns
- `scenario_info` (default: `{}`): the dict of meta data desired by the
                                   developer

Thus, an example instantiation of the logger is as follows:
```
from l2logger import l2logger
...
dir = 'l2_logs'
cols = ['reward']
meta = {'author': 'JHU APL', 'scenario_version': '0.1'}
perf_logger = l2logger.RLPerformanceLogger(dir, cols, meta)
```

### Writing Data

There are two main member functions used to interface with the logger, 
`write_to_blocks_log` and `write_to_data_log`.

`write_to_blocks_log` should typically be called at the start of
a new regime for a given worker.
It sets the "logging context" (i.e. creates the directory
structure for a particular "worker-block-task" combination), as well as
appends a row to the `block-report.tsv` file therein.
Subsequent calls to `write_to_data_log` will use this "logging context" as the
directory in which `data-log.tsv` will be appended to; as such, this function 
**must** be invoked at least once before a call to `write_to_data_log`.

`write_to_blocks_log` has three arguments:
- `record`
    - Python dictionary containing the following entries:
        - `block_num`: int, block sequence index
        - `regime_num`: int, regime sequence index
        - `block_type`: str, e.g. 'train' or 'test'
        - `worker`: str, name of the current worker (e.g. 'thread-1')
        - `task_name`: str, current task (e.g. 'Task-A-5x5')
        - `params`: str, JSON string of any parameters for the task ('size', etc.)
    - The `*_num` fields are all globally incrementing, zero-indexed counts
    - If more fields are provided than these, then they will simply be output
      as additional columns
- `directory_info`
    - Python dictionary containing the following entries, for logging context:
        - `scenario_dirname`: str, as described above, folder name for this run
                              of the scenario
        - `worker_dirname`: str, the folder name to create for the current worker
        - `block_dirname`: str, folder name to create for the current block. 
                    Suggested some combination of `block_num` and `block_type`
- `update_context_only` (default `False`)
    - Flag to indicate whether to only change/create logging context, rather than
      doing so and also appending to the blocks log.
    - Still requires the full `directory_info` as well as `task_name` in `record`
    - Not recommended except for advanced usage


`write_to_data_log`, as mentioned above, assumes that the logging context has
already been created/switched to. It should be invoked at least once per
individual experience.

`write_to_data_log` requires a single argument:
- `record`
    - Python dictionary containing the following entries:
        - `block_num`: int, block sequence index
        - `regime_num`: int, regime sequence index
        - `exp_num`: int, experience sequence index
        - `status`: str, current experience status (e.g. 'Done'). 
            - **This field is only required for `RLPerformanceLogger`,
              not `ClassifPerformanceLogger`**
        - `timestamp`: str, current timestamp. Suggested to get through 
            `PerformanceLogger.get_readable_timestamp`, described below.
    - Again, the `*_num` fields are all globally incrementing, zero-indexed
      counts; the `block_num` and  `regime_num` fields should match those in
      the blocks log entry
    - Again, if more fields are provided than these, then they will simply be
      output as additional columns. This includes common (but not standard) 
      fields such as 'reward' or 'random_seed'

For a more comprehensive example of usage of this interface, please look at the
examples as explained below.

### Utils

The performance logger provides several utility functions which may be useful
to the developer. These include:

- `PerformanceLogger.get_readable_timestamp(cls)`
    - class method in PerformanceLogger which returns a human readable string
      of the current time. Useful for the `timestamp` column in data records:
    ```
    ts = l2logger.PerformanceLogger.get_readable_timestamp()
    ```
- `PerformanceLogger.toplevel_dir`
    - property returning the top level directory that was passed into the
    logger's constructor:
    ```
    root_dir = logger_obj.toplevel_dir
    ```
- `PerformanceLogger.logging_dir`
    - property returning the current logging directory, as in the top level
    directory + the subfolder structure to get to the current log files:
    ```
    log_dir = logger_obj.logging_dir
    # e.g. 'logs/a-1600697775-609517/thread-0/0-train/A'
    ```


## Examples

### mock_ml_workflow

Demonstrates a very simple mock RL workflow which would utilize the logger
library. Consists of three files:
- `driver.py`:
    - The main script for the example; creates the logger object and
    contains all interfacing calls with it
- `mock_agent.py`:
    - A helper file to manage the RL "magic" side of things, e.g. parsing
    an example scenario input file, managing the `block_num`, `regime_num`, 
    `exp_num` sequences as it goes.
    - Contains excessively simple `Experience` class representing an RL task;
    upon invocation, just returns hardcoded 'reward' and 'debug_info' columns.
- `simple_scenario.json`
    - An invented format for representing a learning/testing scenario; also
    contains the top level dir (*relative to current working directory*), in
    which the scenario directory will be made

Ensure the l2 virtual environment is active, then run simply via:
```
cd examples/mock_ml_workflow
python driver.py
```
It will create logs in whichever relative folder is specified in the 
`logging_base_dir` entry within `simple_scenario.json`.
Repeated invocations will create their own scenario folders, with the 
timestamp included as part of the name, as suggested.

### trivial

Demonstrates usage of multiprocessing with the logging library; is very much 
a work in progress, but demonstrates the usefulness of having each worker have 
its own folder within the scenario directory.

Ensure the l2 virtual environment is active, then run simply via:
```
cd examples/trivial
python trivial_example.py input_trivial.json
```
It will create logs in whichever relative folder is specified in the 
`logging_base` field within `input_trivial.json`

### Tips
Make sure to not add logs in example to git