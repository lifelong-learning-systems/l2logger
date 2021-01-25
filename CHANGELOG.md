# Changelog

All notable changes to this repository are documented here. We are using [Semantic Versioning for Documents](https://semverdoc.org/), in which a version number has the format `major.minor.patch`.

## 1.0.5 - 2021-01-25

- Added handling for forward/backward slashes in log directory command-line argument

## 1.0.4 - 2021-01-11

- Added directory and path validation when reading log data
- Added docstrings for utility functions
- Specified minimum pandas version
- Converted all task names to lowercase when reading log data
- Fixed handling of NaN task parameters

## 1.0.3 - 2020-12-29

- Fixed typo in L2Logger init filename

## 1.0.2 - 2020-12-15

- Added warnings in scenario info validation
- Truncated task parameters in summary table of log validation
- Added type hints
- Used pathlib to handle file paths
- Cleaned up imports

## 1.0.1 - 2020-11-30

- Added complexity and difficulty to scenario information

## 1.0.0 - 2020-10-21

- Updated API, largely centered around simplification
- Only requires a single logging function now (log_record) rather than the
  previous two (write_new_regime and write_to_data_log)
- Removed requirement of user provided regime_num; is now automatically
  calculated when loading metrics
- Added more ongoing validation during the logging process

## 0.1.0 - 2020-09-23

- Initial release
- See [README.md](./README.md) for documentation, examples, and unit tests
