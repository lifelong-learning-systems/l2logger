# Lifelong Learning Logger Output Format

This document describes the `l2logger` output format in terms of the
directory structure created and the contents of the files therein. This is
***version `1.0`*** of the `log_output_format`.

## Directory Structure
The logger produces output according to the structure below. At
instantiation, the logger takes in `logging_base_dir` to start as the 
top-level logging directory, creating it if it doesn't exist already.

```
logging_base_dir
└───scenario_dir
    │   scenario_info.json
    │   logger_info.json
    │
    └───worker-0
    │   └───block-0
    │   │    │   data-log.tsv
    │   ...
    │   │
    │   └───block-n
    │        │   data-log.tsv
    │    
    │   
    ...   
    └───worker-m
    │   └───block-0
    │   │    │   data-log.tsv
    │   ...
    │   │
    │   └───block-n
    │        │   data-log.tsv
    │   ...
    ...
``` 


From the directory structure, `scenario_dir` should be the name of a 
specific run of a given scenario (e.g. the scenario name followed by a
timestamp, like `simple-1600697775-609517`).
Within this folder are `scenario_info.json` and `logger_info.json`; see
the 'Initialization' section in [interface.md](./interface.md) for
explanation of their contents.

Still within this top-level scenario directory, each
worker (e.g. thread or process) then gets its own folder to write logs to.
Within a worker's folder, there is a folder for each block in the syllabus
that the worker consumed experiences on (e.g. '0-train', '1-test', etc). 
Then, within each of these folders, is the `data-log.tsv` file containing
the actual logged records for that (worker, block) pair.

The interface for providing this information to the logger, as well as 
details on the contents of the TSV files, is explained in
more detail in [interface.md](./interface.md) as well as below.

## data-log.tsv format

`data-log.tsv` is a tab-separated value file. It expects the first line
to contain the column headers, then each subsequent line to contain values
for each column separated by tabs. For a raw example of what this file
should look like, see [here](../examples/example_data_log.tsv)

Important to note about this format:
- `task_params` is the result of calling `json.dumps(...)` on the params
  field in the record; as a result, the escaping of quotes and other
  special characters therein are rather particular.
- `timestamp` is the result of formatting `datetime.now()` with the 
  time format string `%Y%m%dT%H%M%S.%f`
    - This is effectively year, month, day followed by hour, minute, second
      with the fractional portion of the second as a single-precision float
    - for example: `20201020T230415.363982`
- all other fields are just dumped in as passed in, integers and strings
  alike, not needing any quotes or escape sequences
