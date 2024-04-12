import typing
from leet import runner
from .python3 import Python3Runner

LANG_TO_RUNNER: typing.Dict[str, typing.Type[runner.Runner]] = {
    'python3': Python3Runner,
}