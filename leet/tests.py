import dataclasses
import pathlib
import tomllib
import typing
from leet import runner

@dataclasses.dataclass
class Tests:
    function: str
    language: typing.Optional[str] = None
    tests: typing.List[runner.Test] = dataclasses.field(default_factory=list)
    
    @classmethod
    def from_file(cls, file: pathlib.Path) -> "Tests":
        """
        Parameters
        ----------
        cls
        file: default = None

        Returns
        -------
        Configuration
        """
        content = tomllib.loads(pathlib.Path(file).read_text())
        return cls(
            function=content.get("function", ""),
            language=content.get("language", None),
            tests=[runner.Test(**test) for test in content.get("tests", [])]
        )
