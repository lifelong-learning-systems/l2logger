# Changelog

All notable changes to this repository are documented here. We are using [Semantic Versioning for Documents](https://semverdoc.org/), in which a version number has the format `major.minor.patch`.

## 1.6.0 - 2021-12-07

- Updated position of regime_num column
- Created module for combining TSV data files and exporting to Feather or CSV
- Added a license file
- Added ste as valid scenario type
- Cleaned up scenario info validation

## 1.5.0 - 2021-10-18

- Updated README and copyright statements

## 1.4.0 - 2021-08-09

- Added support for variant-agnostic calculations by modifying task parameter usage in regime identification

## 1.3.0 - 2021-07-27

- Added support for additional scenario types (condensed, dispersed)

## 1.2.1 - 2021-05-17

- Updated regime fill to look for changes in block subtype

## 1.2.0 - 2021-05-11

- Added support for block subtypes (wake, sleep)
- Updated documentation and log format version number

## 1.1.0 - 2021-04-12

- Optimized logger utility performance with numpy vectorization
- Modified log directory to be positional argument in validation module
- Simplified block parsing algorithm
- Added handling of scenario type in scenario info file
- Added check for task naming format
- Return entire dictionaries for logger info and scenario info function
- Replaced os path calls with pathlib

## 1.0.7 - 2021-03-01

- Added block number change as additional signal for regime change
- Added log validation script as package module

## 1.0.6 - 2021-02-08

- Fixed bug with performing string operations on Path object in log validation script
- Sorted log data by block number in addition to experience number to handle false  log invalidation due to distributed systems

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
