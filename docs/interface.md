
# Lifelong Learning Logger Interface/Usage

## Initialization

The logger is instantiated by creating an instance of the `DataLogger` class 

The logger takes four input arguments, with the last one optional.
- `logging_base_dir`:
  - This is the highest level directory, as visualized in
  [log_format.md](./log_format.md)
  - For example, this could be the `L2DATA` environment variable, which you
    can get via the provided util function `get_l2data_root` below
- `scenario_name`:
  - The name of the current scenario which is running.
  - This will be appended with a human readable timestamp upon
    initialization of the object to form the `scenario_dir`, as 
    shown in [log_format.md](./log_format.md)
- `logger_info`:
    - dict of column data desired by the developer. Object is required to
    contain at minimum 'metrics_columns', a list of columns which metrics can
    be computed on. Note that this list cannot be empty.
    - See [here](../examples/example_logger_info.json) for an example file
    - This is primarily used as a validation step in the `l2metrics` module
        - It's also validated that all of these fields exist in the record
        passed in to the `log_record` function below
    - The logger will also add the field `log_format_version` with the
      format version as defined in [log_format.md](./log_format.md)
      automatically
- `scenario_info` (default: `{}`):
  - the dict of meta data desired by the developer. There are no requirements
  on what this object contains, but for example could be 'author', or 'version'
  - See [here](../examples/example_scenario_info.json) for an example file

Thus, an example instantiation of the logger is as follows:
```
from l2logger import l2logger
...
dir = 'l2_logs'
name = 'test_scenario'
cols = ['reward']
meta = {'author': 'JHU APL', 'scenario_version': '0.1'}
perf_logger = l2logger.DataLogger(dir, name, cols, meta)
```

## Writing Data

The function used to actually write data into the log is 
`log_record`. This takes in a python object containing at minimum
the following fields: 
- `block_num`
- `exp_num`
- `worker_id`
- `block_type`
- `task_name`
- `task_params`
- `exp_status`

Any additional fields will simply be appended as their own columns in
alphabetical order after these. This **also** needs to include all of the
fields from the `metrics_columns` list within the `logger_info` provided at
instantiation to the logger. Additionally note that every call to this 
function needs to contain **exactly the same** columns as the first call, 
and that a `timestamp` column is automatically provided by the logger.

Here's a deeper dive on the constraints and description of each field:
- `block_num`
  - a non-negative integer
  - cannot be less than the previous `block_num`
  - note that this function is not thread-safe, so if used in a
    multi-threaded context will require synchronization on the caller
    side
- `exp_num`
  - same constraint as above; non-negative, non-decreasing integer
- `worker_id`
  - string; can only contain alphanumeric characters, hyphens, 
    dashes, and periods.
  - if not provided, will *default* to 'worker-default'
- `block_type`
  - string; can only be one of 'train' or 'test'
- `task_name`
  - string; no restrictions
- `task_params`
  - dict; must be JSON serializable (can have `json.dumps(...)` invoked)
- `exp_status`
  - string; must be one of 'complete' or 'incomplete'
  - if not provided, will *default* to 'complete'
  - note that exactly one call to `log_record` for a specific `exp_num` 
    should have the `exp_status` of 'complete'
      - this indicates to the `l2metrics` module which row to pull the
        reward value from, if there were multiple to choose from for a
        specific `exp_num`
  

For a more comprehensive example of usage of this interface, please look
at the examples as explained [here](../examples/README.md).

## Closing log files

When the program is complete, you should invoke the `close` function on the
DataLogger object, i.e.:
```
logger = l2logger.DataLogger(...)
# do RL tasks
...
logger.close()
```

## Utils

The performance logger provides several utility functions which may be useful
to the developer. These include:

- `DataLogger.get_readable_timestamp(cls)`
    - class method in DataLogger which returns a human readable string
      of the current time. Useful for the `timestamp` column in data records:
    ```
    ts = l2logger.DataLogger.get_readable_timestamp()
    ```
- `DataLogger.logging_base_dir`
    - property returning the top level directory that was passed into the
    logger's constructor:
    ```
    root_dir = logger_obj.logging_base_dir
    ```
- `DataLogger.scenario_dir`
    - property returning the scenario directory created, as in the
      `logging_base_dir` followed by the scenario name and generated,
       readable timestamp
    ```
    log_dir = logger_obj.scenario_dir
    # e.g. 'logs/scenario-1600697775-609517/'
    ```

- `util.get_l2data_root`
    - returns the root directory where L2 data and logs are saved via the 
      environment variable "L2DATA":
    ```
    logging_base_dir = util.get_l2data_root()
    ```