# Lifelong Learning Logger (L2Logger)

The Lifelong Learning Logger is a utility library provided for
producing logs in a convenient format for the provided l2metrics module,
but can also be used independently.

## Logger Term Definitions/Glossary

Strongly recommend starting here, detailed explanation of the terms used
throughout: [docs/definitions.md](./docs/definitions.md).

## Logger Output Format

Detailed explanations of the logging output structure/format can be seen via
[docs/log_format.md](./docs/log_format.md).

## Interface/Usage

At a high level, the library is used simply by creating an
instance of the logger object, then by invoking the `log_record`
 member function on it at least once per experience.

For a detailed explanation of the provided functions, see
[docs/interface.md](./docs/interface.md).

## Examples

See documentation in the examples folder at [examples/README.md](./examples/README.md).

## Tests

See documentation in the test folder at [test/README.md](./test/README.md).

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for a list of notable changes to the
project.
