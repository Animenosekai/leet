import abc
import dataclasses
import pathlib
import tempfile
import time
import typing
import uuid

import psutil


@dataclasses.dataclass
class Test:
    arguments: typing.Dict[str, typing.Any]
    expected: typing.Any
    explanation: typing.Optional[str] = None

    def to_dict(self) -> dict:
        """
        Returns
        -------
        dict
        """
        return {
            "arguments": self.arguments,
            "expected": self.expected,
            "explanation": self.explanation,
        }


class Runner(abc.ABC):
    HEADER: str
    "This will be prepended at the beginning of the solution and should contain all the imports and definitions needed to match LeetCode's environment."
    FOOTER: str
    "This will be appended at the end of the solution and should perform all the tests. This takes `run_id`, `tests` and `function_name` as arguments."

    @classmethod
    def run(
        cls,
        code: str,
        function_name: str,
        tests: typing.List[Test],
        run_id: typing.Optional[str] = None,
    ) -> typing.Tuple[float, float, float]:
        """
        Runs the given code with the given tests.

        Parameters
        ----------
        cls
        code: str
        function_name: str
        tests: List[Test] | list
        run_id: NoneType | str, default = None

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
    def run_file(cls, file: pathlib.Path) -> typing.Tuple[float, float, float]:
        """
        Just runs the given file.

        Parameters
        ----------
        cls
        file: Path

        Returns
        -------
        tuple
            A tuple with the time taken, peak CPU usage and peak memory usage.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def encode_tests(cls, tests: typing.List[Test]) -> str:
        """
        Parameters
        ----------
        cls
        tests: list

        Returns
        -------
        str
        """
        pass

    @classmethod
    @abc.abstractmethod
    def get_executable(cls) -> str:
        """
        Parameters
        ----------
        cls

        Returns
        -------
        str
        """
        pass

    @classmethod
    def create_file(
        cls,
        code: str,
        function_name: str,
        tests: typing.List[Test],
        run_id: typing.Optional[str] = None,
    ):
        """
        Creates a file with the given tests.

        Parameters
        ----------
        cls
        code: str
        function_name: str
        tests: List[Test] | list
        run_id: NoneType | str, default = None
        """
        run_id = run_id or str(uuid.uuid4())
        run_id = run_id.replace("-", "_")
        run_id = "".join([l for l in run_id if l.isalnum() or l == "_"])
        return (
            run_id,
            f"{cls.HEADER}\n\n{code}\n\n{cls.FOOTER.format(run_id=run_id, tests=cls.encode_tests(tests), function_name=function_name)}\n        ",
        )

    @classmethod
    def execute(cls, *args):
        """
        Parameters
        ----------
        cls
        args
        """
        peak_cpu = 0
        peak_memory = 0
        proc = psutil.Popen(args)
        start = time.perf_counter_ns()
        try:
            while proc.is_running():
                peak_cpu = max(peak_cpu, proc.cpu_percent() / (psutil.cpu_count() or 1))
                peak_memory = max(peak_memory, proc.memory_info().rss)
        except Exception:
            pass
        # time = proc.cpu_times().user + proc.cpu_times().system
        return ((time.perf_counter_ns() - start) / 1000000.0, peak_cpu, peak_memory)

    @classmethod
    def function_location_from_name(cls, function_name: str, boilerplate: str) -> str:
        """
        Parameters
        ----------
        cls
        function_name: str

        Returns
        -------
        str
        """
        return function_name

class CompiledRunner(Runner):
    @classmethod
    @abc.abstractmethod
    def compile(cls, file: pathlib.Path, to: pathlib.Path):
        """
        Compiles the given file.

        Parameters
        ----------
        cls
        file: Path
        to: Path
        """
        pass

    @classmethod
    def run_file(cls, file: pathlib.Path) -> typing.Tuple[float, float, float]:
        """
        Parameters
        ----------
        cls
        file: Path

        Returns
        -------
        tuple
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = pathlib.Path(temp_dir) / f"{file.stem}-{uuid.uuid4()}"
            cls.compile(file, temp_file)
            return cls.execute(temp_file)

