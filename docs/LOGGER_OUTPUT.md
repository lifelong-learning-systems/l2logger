# Lifelong Learning Logger Output and Structure

## Definitions

This module assumes the following nomenclature for the hierarchical
organization of tasks:

- `Scenario`: the overall sequence of `blocks`, typically alternating  
               between training and testing
- `Block`: a sequence of `regimes`, all with the same block type (i.e. train or test)
- `Regime`: a sequence of `experiences`, all with the same parameters and name
- `Experience`: a specific instance of a task (e.g. an instance of a gym
                environment of the given name, with the provided parameters)

## Directory Structure
The logger produces output according to the structure below. At
instantiation, the logger takes in `logging_base_dir` to start as the 
top-level logging directory, creating it if it doesn't exist already.

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


From the directory structure, `scenario_dirname` should be the name of a 
specific run of a given scenario (e.g. the scenario name followed by a
timestamp, like `simple-1600697775-609517`).
Within this folder are `scenario_info.json` and `column_metric_list.json`:
- Scenario info is a file for any meta-data the developer wishes
to output along with the logs (e.g. 'author', or 'scenario-version'). 
- Column metric list consists of a list of which data columns metrics may
  be computed upon (e.g. 'reward').
  This is primarily used by `l2metrics` as a validation step

Still within this top-level scenario directory, each
worker (e.g. thread or process) then gets its own folder to write logs to.
Within a worker's folder, there is a folder for each block in the syllabus
that the worker consumed experiences on (e.g. '0-train', '1-test', etc). 
Within these block directories, there are then folders for each different task
that these consumed experiences entailed (e.g. 'Env-A-5x5', 'Env-B-2x2', etc.).
Finally within these task folders are the actual TSV log files: 
`block-report.tsv` and `data-log.tsv`. 

The interface for providing this information to the logger, as well as 
details on the contents of the TSV files, is explained in
more detail in [INTERFACE.md](./INTERFACE.md)
