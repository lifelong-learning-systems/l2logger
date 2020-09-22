
# Lifelong Learning Logger Interface/Usage

## Initialization

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

## Writing Data

There are two main member functions used to interface with the logger, 
`write_to_blocks_log` and `write_to_data_log`.

### `write_to_blocks_log`:
This function should typically be called at the start of
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


### `write_to_data_log`:
This function, as mentioned above, assumes that the logging context has
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
examples as explained [here](../examples/README.md).

## Utils

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