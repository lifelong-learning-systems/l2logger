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

### Utils


## Examples
### Tips
Make sure to not add logs in example to git