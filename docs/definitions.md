# Lifelong Learning Logger Term Definitions/Glossary

## Definitions

This module assumes the following nomenclature for the hierarchical
organization of tasks:

- `Experience`: a specific instance of a task (e.g. an instance of a gym
                environment of the given name, with the provided parameters)
  - Have a globally incrementing sequence number, `exp_num`
- `Regime`: a sequence of `experiences`, all with the same parameters and task
  - Have a globally incrementing sequence number, `regime_num`
- `Block`: a sequence of one or more `regimes`, all with the same associated type
  - Have a globally incrementing sequence number, `block_num`
  - Have a `block_type`, which should be 'train' or 'test'
  - Blocks have names assumed to be their global number followed by their type
    (e.g. '0-train', '1-test', '2-train', etc.)
- `Scenario`: the overall sequence of `blocks`, typically alternating  
               between training and testing

You can think of `blocks` as groups of either training (learning) or 
testing (evaluating). Whenever you wish to switch from one type to the
next, you thus need a new block.

`Regimes` can be thought of as smaller groups within blocks; if you want to
switch from training on Task A to Task B, or run Task A with new parameters,
then you need a new regime.

## Example

As an example, if you wanted to learn on 100 episodes of Task_A, then
evaluate on 50 episodes of Task_A as well as Task_B, then the terms above
would apply as such:
- `Scenario`
  - `Block`
    - block_num: 0
    - type: 'train'
    - `Regime`
      - regime_num: 0
      - 100 repetitions of Task_A, with desired parameters
      - `Experiences`:
         - exp_num: 0-99
         - actually run/update model on an episode of Task_A 
  - `Block`
    - block_num: 1
    - type: 'test'
    - `Regime`
      - regime_num: 1
      - 50 repetitions of Task_A, with desired parameters
      - `Experiences`:
         - exp_num: 100-149
         - actually run/evaluate model on an episode of Task_A 
    - `Regime`
      - regime_num: 2
      - 50 repetitions of Task_B, with desired parameters
      - `Experiences`:
         - exp_num: 150-199
         - actually run/evaluate model on an episode of Task_B