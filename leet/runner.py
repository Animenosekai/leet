"""Module containing the base runner classes and testing structures."""

from __future__ import annotations

import abc
import contextlib
import dataclasses
import pathlib
import tempfile
import time
import typing
import uuid

import psutil
from typing_extensions import override


@dataclasses.dataclass
class Test:
    """A class representing a single test case."""

    arguments: dict[str, typing.Any]
    expected: typing.Any
    explanation: str | None = None

    def to_dict(self) -> dict[str, typing.Any]:
        """
        Convert the test case to a dictionary.

        Returns
        -------
        dict[str, typing.Any]
        """
        return {
            "arguments": self.arguments,
            "expected": self.expected,
            "explanation": self.explanation,
        }


class Runner(abc.ABC):
    """An abstract class representing a runner for a specific language."""

    HEADER: str
    "Header prepended to the solution with all environment imports and definitions."
    FOOTER: str
    "Footer appended to the solution to execute the tests."

    @classmethod
    def run(
        cls,
        code: str,
        function_name: str,
        tests: list[Test],
        run_id: str | None = None,
    ) -> tuple[float, float, float]:
        """
        Run the given code with the given tests.

        Parameters
        ----------
        cls
        code: str
            The code to run.
        function_name: str
            The name of the function to test.
        tests: list[Test]
            The list of tests to run.
        run_id: str | None, default = None
            The run ID to use.

        Returns
        -------
        tuple
            A tuple with the time taken, peak CPU usage and peak memory usage.
        """
        run_id, content = cls.create_file(code, function_name, tests, run_id)
        with tempfile.TemporaryDirectory() as temp_dir:
            file = pathlib.Path(temp_dir) / run_id
            file.write_text(content)
            return cls.run_file(file)

    __call__ = run

    @classmethod
    @abc.abstractmethod
    def run_file(cls, file: pathlib.Path) -> tuple[float, float, float]:
        """
        Run the given file.

        Parameters
        ----------
        cls
        file: pathlib.Path
            The path to the file to run.

        Returns
        -------
        tuple
            A tuple with the time taken, peak CPU usage and peak memory usage.
        """

    @classmethod
    @abc.abstractmethod
    def encode_tests(cls, tests: list[Test]) -> str:
        """
        Encode the given tests into a string.

        Parameters
        ----------
        cls
        tests: list[Test]
            The list of tests to encode.

        Returns
        -------
        str
        """

    @classmethod
    @abc.abstractmethod
    def get_executable(cls) -> str:
        """
        Return the path to the executable to use for the runner.

        Parameters
        ----------
        cls

        Returns
        -------
        str
        """

    @classmethod
    def create_file(
        cls,
        code: str,
        function_name: str,
        tests: list[Test],
        run_id: str | None = None,
    ) -> tuple[str, str]:
        """
        Create a file with the given code and tests.

        Parameters
        ----------
        cls
        code: str
            The code to write to the file.
        function_name: str
            The name of the function to test.
        tests: list[Test]
            The list of tests to encode.
        run_id: str | None, default = None
            The run ID to use.
        """
        run_id = run_id or str(uuid.uuid4())
        run_id = run_id.replace("-", "_")
        run_id = "".join([char for char in run_id if char.isalnum() or char == "_"])
        footer = cls.FOOTER.format(
            run_id=run_id,
            tests=cls.encode_tests(tests),
            function_name=function_name,
        )
        return (
            run_id,
            f"{cls.HEADER}\n\n{code}\n\n{footer}\n        ",
        )

    @classmethod
    def execute(cls, *args: str | pathlib.Path) -> tuple[float, float, float]:
        """
        Execute the given command and returns performance metrics.

        Parameters
        ----------
        cls
        args: str | pathlib.Path
            The command to execute.
        """
        peak_cpu = 0
        peak_memory = 0
        proc = psutil.Popen(args)
        # First call to cpu_percent returns 0, we need it to initialize
        proc.cpu_percent()
        start = time.perf_counter_ns()
        with contextlib.suppress(Exception):
            while proc.is_running():
                peak_cpu = max(
                    peak_cpu,
                    proc.cpu_percent() / (psutil.cpu_count() or 1),
                )
                peak_memory = max(peak_memory, proc.memory_info().rss)
                time.sleep(0.001)
        # time = proc.cpu_times().user + proc.cpu_times().system
        return (
            (time.perf_counter_ns() - start) / 1000000.0,
            peak_cpu,
            peak_memory,
        )

    @classmethod
    def function_location_from_name(cls, function_name: str, boilerplate: str) -> str:
        """
        Return the location of the function in the boilerplate.

        Parameters
        ----------
        cls
        function_name: str
            The name of the function.
        boilerplate: str
            The boilerplate code.

        Returns
        -------
        str
        """
        del boilerplate
        return function_name


class CompiledRunner(Runner):
    """An abstract class representing a compiled runner."""

    @classmethod
    @abc.abstractmethod
    def compile(cls, file: pathlib.Path, to: pathlib.Path) -> None:
        """
        Compile the given file.

        Parameters
        ----------
        cls
        file: pathlib.Path
            The path to the file to compile.
        to: pathlib.Path
            The path to the compiled file.
        """

    @classmethod
    @override
    def run_file(cls, file: pathlib.Path) -> tuple[float, float, float]:
        """
        Compile and run the given file.

        Parameters
        ----------
        cls
        file: pathlib.Path
            The path to the file to run.

        Returns
        -------
        tuple
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = pathlib.Path(temp_dir) / f"{file.stem}-{uuid.uuid4()}"
            cls.compile(file, temp_file)
            return cls.execute(temp_file)
