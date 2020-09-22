# Lifelong Learning Logger Examples

## mock_ml_workflow

Demonstrates a very simple mock RL workflow which would utilize the logger
library. Consists of three files:
- `driver.py`:
    - The main script for the example; creates the logger object and
    contains all interfacing calls with it
- `mock_agent.py`:
    - A helper file to manage the RL "magic" side of things, e.g. parsing
    an example scenario input file, managing the `block_num`, `regime_num`, 
    `exp_num` sequences as it goes.
    - Contains excessively simple `Experience` class representing an RL task;
    upon invocation, just returns hardcoded 'reward' and 'debug_info' columns.
- `simple_scenario.json`
    - An invented format for representing a learning/testing scenario; also
    contains the top level dir (*relative to current working directory*), in
    which the scenario directory will be made

Ensure the l2 virtual environment is active, then run simply via:
```
cd mock_ml_workflow
python driver.py
```
It will create logs in whichever relative folder is specified in the 
`logging_base_dir` entry within `simple_scenario.json`.
Repeated invocations will create their own scenario folders, with the 
timestamp included as part of the name, as suggested.

## trivial

Demonstrates usage of multiprocessing with the logging library; is very much 
a work in progress, but demonstrates the usefulness of having each worker have 
its own folder within the scenario directory.

Ensure the l2 virtual environment is active, then run simply via:
```
cd trivial
python trivial_example.py input_trivial.json
```
It will create logs in whichever relative folder is specified in the 
`logging_base` field within `input_trivial.json`

## Tips
Make sure to not add logs in example to git