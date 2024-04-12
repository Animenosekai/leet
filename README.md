# leet

Let's solve LeetCode problems with fun ⛑️

This command line tool lets you solve LeetCode problems locally.

## Index

- [Index](#index)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Run](#run)
  - [Download](#download)
- [Configuration](#configuration)
- [Runners](#runners)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Authors](#authors)
- [License](#license)

## Features

- Download problems from LeetCode
- Download daily problem from LeetCode
- Download boilerplate code for a problem
- Download test cases for a problem
- Run test cases for a problem, mimickig the LeetCode environment

## Installation

```bash
pip install --upgrade git+https://github.com/Animenosekai/leet.git
```

## Usage

```bash
usage: leet [-h] {run,download} ...

Solve LeetCode problems with fun ⛑️

positional arguments:
  {run,download}

options:
  -h, --help      show this help message and exit
```

### Run

```bash
usage: leet run [-h] [--language LANGUAGE] [--dry] [file]

Run a file using the same environment as on LeetCode.

positional arguments:
  file                  The file to run.

options:
  -h, --help            show this help message and exit
  --language LANGUAGE, -l LANGUAGE
                        The language to use. If not provided, inferred from the file extension.
  --dry                 Generates a file which can be ran to test the function.
```

### Download

```bash
usage: leet download [-h] [--output OUTPUT] [--language LANGUAGE] {all,solutions,problem,boilerplate,tests} ... [problem]

Download a problem.

positional arguments:
  {all,solutions,problem,boilerplate,tests}
  problem               The problem URL or slug.

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        The output path.
  --language LANGUAGE, -l LANGUAGE
                        The language to use. If not provided, inferred from the file extension. If impossible, defaults to 'python3'.
```

## Configuration

You can configure the tool by creating a `leet.toml` file in the current directory.

```toml
[download]
language = "python3" # the default language to use when it's not inferred
output = "problems" # the default output directory
```

You can also configure tests by creating a `tests.toml` file in the problem directory.

```toml
# Default language to use for the tests
language = "python3"

# The function to test
[function]
"*" = "isValid"
python3 = "Solution().isValid"

# A single value `function = "<func_name>"` can also be provided and treated as a wildcard

[[tests]]
arguments = { "s" = "()" }
expected = true
explanation = "This is a valid parenthesis pattern."

[[tests]]
arguments = { "s" = "(]" }
expected = false

[[tests]]
expected = true

[tests.arguments]
s = "()[]{}"
```

## Runners

You can have an in-depth understanding of the running environments by looking at their respective explanation file :

- [Python 3](./leet/runners/python3.md)

## Deployment

This module is currently in development and might contain bugs.

Feel free to use it in production if you feel like it is suitable for your production even if you may encounter issues.

## Contributing

Pull requests are welcome. For major changes, please open a discussion first to discuss what you would like to change.

Please make sure to update the tests as appropriate.

## Authors

- **Anime no Sekai** — *Initial work* — [Animenosekai](https://github.com/Animenosekai)

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
