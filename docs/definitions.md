# Lifelong Learning Logger Term Definitions/Glossary

## Definitions

This module assumes the following nomenclature for the hierarchical
organization of tasks:

- `Experience`: a specific instance of a task (e.g. an instance of a gym
                environment of the given name, with the provided parameters)
- `Block`: a sequence of experiences, all with the same associated "`block_type`":
  - Have a `block_type`, which should be 'train' or 'test'
  - Blocks have names assumed to be their global number followed by their type
    (e.g. '0-train', '1-test', '2-train', etc.)
  - The task name and parameters can change within a block; the constraint
    here is that changing between 'train' and 'test' requires
    incrementing the `block_num`
- `Scenario`: the overall sequence of `blocks`, typically alternating  
               between training and testing

You can think of `blocks` as groups of either training (learning) or
testing (evaluating). Whenever you wish to switch from one type to the
next, you thus need a new block.

## Example

As an example, if you wanted to learn on 100 episodes of Task_A, then
evaluate on 50 episodes of Task_A as well as Task_B, then the terms above
would apply as such:

- `Scenario`
  - `Block`
    - block_num: 0
    - type: 'train'
    - 100 repetitions of Task_A, with desired parameters
      - `Experiences`:
        - exp_num: 0-99
        - actually run/update model on an episode of Task_A
  - `Block`
    - block_num: 1
    - type: 'test'
    - 50 repetitions of Task_A, with desired parameters
      - `Experiences`:
        - exp_num: 100-149
        - actually run/evaluate model on an episode of Task_A
    - 50 repetitions of Task_B, with desired parameters
      - `Experiences`:
        - exp_num: 150-199
        - actually run/evaluate model on an episode of Task_B
