# Lifelong Learning Logger Output/Structure

## Directory Structure
The logger produces output according to the structure below. At
instantiation, the logger takes in `logging_base_dir` to start as the 
top-level logging directory, creating it if it doesn't exist already.

```
logging_base_dir
└───scenario_dirname
    │   scenario_info.json
    │   column_info.json
    │
    └───worker-0
    │   └───block-0
    │   │    └───task-0
    │   │    │    │   block-info.tsv
    │   │    │    │   data-log.tsv
    │   │    │ 
    │   │    ...
    │   │    │
    │   │    └───task-n
    │   │         │   block-info.tsv
    │   │         │   data-log.tsv
    │   ...
    │   │
    │   └───block-n
    │        └───task-0
    │        │    │   block-info.tsv
    │        │    │   data-log.tsv
    │        │ 
    │        ...
    │        │
    │        └───task-n
    │             │   block-info.tsv
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
Within this folder are `scenario_info.json` and `column_info.json`; see
the 'Initialization' section in [interface.md](./interface.md) for
explanation of their contents.

Still within this top-level scenario directory, each
worker (e.g. thread or process) then gets its own folder to write logs to.
Within a worker's folder, there is a folder for each block in the syllabus
that the worker consumed experiences on (e.g. '0-train', '1-test', etc). 
Within these block directories, there are then folders for each different task
that these consumed experiences entailed (e.g. 'Env-A-5x5', 'Env-B-2x2', etc.).
Finally within these task folders are the actual TSV log files: 
`block-info.tsv` and `data-log.tsv`. 

The interface for providing this information to the logger, as well as 
details on the contents of the TSV files, is explained in
more detail in [interface.md](./interface.md) as well as below.
In brief, `block-info.tsv` contains information about the regimes that
were worked in, while `data-log.tsv` contains information about each
experience consumed.


## Example Output

### main_thread/0-train/Task_A/block-info.tsv

block_num | regime_num | block_type | worker | task_name | params
--- | --- | --- | --- | --- | ---
0 | 0 | train | main_thread | Task_A | ["-s", 5]
0 | 1 | train | main_thread | Task_A | ["-s", 10]


### main_thread/0-train/Task_A/data-log.tsv
block_num | regime_num | exp_num | status | timestamp | reward
--- | --- | --- | --- | --- | ---
0 | 0 | 0 | Done | 20200923T115137.150115 | 1 
0 | 0 | 2 | Done | 20200923T115137.150228 | 10
0 | 0 | 4 | Done | 20200923T115137.150637 | 12
0 | 1 | 5 | Done | 20200923T115137.151008 | 4 
0 | 1 | 7 | Done | 20200923T115137.151302 | 5 
0 | 1 | 9 | Done | 20200923T115137.151492 | 7

### Explanation

- Information from the block info file:
    - We can see that the block has two regimes, varying which parameters
    (`params`) have been passed into Task_A (`task_name`)
    - Thus, the `block_num` is 0 and the `regime_num` goes from 0 to 1 as
    well
    - The `worker` is 'main_thread', as shown in both the directory structure
    and the content of the block info file.
- Information from the data log:
    - The `block_num` and `regime_num` match those within the block info file
    - The worker consumed three experiences for each regime
        - Note that all `nums` are increasing globally, never resetting
          back to zero
    - We can infer that there must be another worker as well, since 
      there are missing `exp_nums`: 1, 3, 6, and 8
    - The client decided to pass in one additional column, `reward`, which 
      is interestingly not increasing monotonically