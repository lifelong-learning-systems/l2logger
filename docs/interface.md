
# Lifelong Learning Logger Interface/Usage

## Initialization

The logger is instantiated by creating an instance of one of two sub-classes
of PerformanceLogger:
- RLPerformanceLogger
- ClassifPerformanceLogger

These differ only in the base columns required when writing to the data log.
The logger takes three input arguments, only the first of which is required:
- `toplevel_dir`: this is the `logging_base_dir` as described in
[logger_output.md](./logger_output.md)
- `column_info` (default: `{'metrics_columns':[]}`):
    - dict of column data desired by the developer. Object is required to
    contain at minimum 'metrics_columns', a list of columns which metrics can
    be computed on. This is primarily used by `l2metrics` as a validation step
    - See [here](../examples/example_column_info.json) for an example file
- `scenario_info` (default: `{}`):
  - the dict of meta data desired by the developer. There are no requirements
  on what this object contains, but for example could be 'author', or 'version'
  - See [here](../examples/example_scenario_info.json) for an example file

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
`write_new_regime` and `write_to_data_log`.

Within the records passed into those functions, the `block_num`,
`regime_num`, and `exp_num` fields should all be globally incrementing,
zero-indexed counts:
- The `block_num` and `regime_num` fields in `write_to_data_log` should match those in
  the `write_new_regime` record
- **Note that the client is responsible for incrementing/managing these
  sequences; the l2metrics module relies on them extensively**
    - For details/examples of what these sequences should look like, see
    the 'Example' section within [definitions.md](./definitions.md)
  

### `write_new_regime`:
This function should typically be called at the start of
a new regime for a given worker.
It sets the "logging context" (i.e. creates the directory
structure for a particular "worker-block-task" combination), as well as
appends a row to the `block-report.tsv` file therein.
Subsequent calls to `write_to_data_log` will use this "logging context" as the
directory in which `data-log.tsv` will be appended to; as such, this function 
**must** be invoked at least once before a call to `write_to_data_log`.

`write_new_regime` has two required arguments:
- `record`
    - Python dictionary containing the following entries:
        - `block_num`: int, block sequence index
        - `regime_num`: int, regime sequence index
        - `block_type`: str, e.g. 'train' or 'test'
        - `worker`: str, name of the current worker (e.g. 'thread-1')
        - `task_name`: str, current task (e.g. 'Task-A-5x5')
        - `params`: str, JSON string of any parameters for the task ('size', etc.)
    - If more fields are provided than these in record, they will simply be
    appended as additional columns in blocks-report.tsv. Note that all records
    should have the same number of columns (i.e., if extra fields are
    supplied for one row in the data log, they should be supplied for all the
    other rows as well).
- `scenario_dirname`: str, as described above, folder name for this run of the scenario

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
        - `status`: str, an arbitrary status indicating how the agent
        processed the experience
            - e.g. 'success' for a completed experience, 'env-error' for an error
              in the environment, etc.
            - **This field is only required for `RLPerformanceLogger`,
              not `ClassifPerformanceLogger`**
        - `timestamp`: str, current timestamp. Suggested to get through 
            `PerformanceLogger.get_readable_timestamp`, described below.
            - **If this is *not* provided, then the logger will
            automatically insert this field via `get_readable_timestamp`**
    - Same as above: if more fields are provided than these in record, they
    will simply be appended as additional columns in data-log.tsv. Note that
    all records should have the same number of columns (i.e., if extra fields
    are supplied for one row in the data log, they should be supplied for all
    the other rows as well). This includes common (but not standard) fields
    such as 'reward' or 'random_seed'

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