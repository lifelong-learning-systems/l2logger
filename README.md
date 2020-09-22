# Lifelong Learning Logger (L2Logger)

The Lifelong Learning Logger is a utility library provided for 
producing logs in a convenient format for the provided l2metrics module,
but can also be used independently.


## Logger Output and Structure
Detailed explanations of the logging output structure/format can be seen via
[docs/LOGGER_OUTPUT.md](./docs/LOGGER_OUTPUT.md).

## Interface/Usage
At a high level, the library is used simply by creating an
instance of the logger object, then by invoking the `write_blocks_to_log`
and `write_data_to_log` member functions on it when desired.

For a detailed explanation of the provided functions, see
[docs/INTERFACE.md](./docs/INTERFACE.md)

## Examples
See documentation in the examples folder at [examples/README.md](./examples/README.md)