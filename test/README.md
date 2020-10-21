# Lifelong Learning Logger Tests

There are several unit tests available, in the `test_simple_logging.py` file

Run them simply by ensuring the virtual environment is active, then:
```
cd test
python test_simple_logging.py
```

## Test summaries
- `testErrorInit`
    - tests a variety of erroneous calls to the constructor of DataLogger,
    including:
        - `logger_info` not being a dict
        - `metrics_columns` field not mapping to a list of non-empty strings
        - `metrics_columns` missing as a field
-  `testValidRecord`
    - ensures valid sequences of calls to `log_record` do not throw errors,
    including:
        - logging the same record twice in a row
        - increasing `exp_num`
        - increasing `block_num`
- `testErrorRecord`
    - ensures erroneous sequences of calls to `log_record` do throw errors:
        - missing various expected fields
        - trying to override `timestamp`
        - adding extra columns in a later call
        - invalid sequences of `block_num` and `exp_num`
        - invalid `worker_id`
        - `task_params` not being JSON serializable