import dataclasses
import json
import pathlib
import tomllib
import typing

import bs4
import pycparser
import pycparser.c_ast
import toml
from leet import runner


@dataclasses.dataclass
class Tests:
    function: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    language: typing.Optional[str] = None
    tests: typing.List[runner.Test] = dataclasses.field(default_factory=list)

    @classmethod
    def from_file(cls, file: pathlib.Path) -> "Tests":
        """
        Parameters
        ----------
        cls
        file: Path, default = None

        Returns
        -------
        Tests
        """
        content = tomllib.loads(pathlib.Path(file).read_text())
        func = content.get("function", {})
        if isinstance(func, str):
            func = {"*": func}
        return cls(
            function=func or {},
            language=content.get("language", None),
            tests=[runner.Test(**test) for test in content.get("tests", [])],
        )

    def to_dict(self) -> dict:
        """
        Returns
        -------
        dict
        """
        return {
            "function": self.function,
            "language": self.language,
            "tests": [test.to_dict() for test in self.tests],
        }

    def dumps(self) -> str:
        """
        Parameters
        ----------
        cls

        Returns
        -------
        str
        """
        return toml.dumps(self.to_dict())


def decode_value(content: str) -> typing.Any:
    """
    Parameters
    ----------
    content: str
        The content to decode

    Returns
    -------
    Any
        The decoded content
    """
    content = str(content).strip()
    try:
        return json.loads(content)
    except Exception:
        return content


def extract_tests(html_content: str) -> typing.List[runner.Test]:
    """
    Parameters
    ----------
    html_content: str
        The html_content HTML

    Returns
    -------
    list
    """
    tests = []
    soup = bs4.BeautifulSoup(html_content, "html.parser")
    for example in soup.find_all("strong", {"class": "example"}):
        example: bs4.PageElement
        input_element = example.parent.find_next_sibling("pre").find("strong")
        args = input_element.find_next_sibling(string=True).text
        decoded_arguments = {
            key.strip(): decode_value(value)
            for key, _, value in [arg.partition("=") for arg in args.split(", ")]
        }
        output_element = input_element.find_next_sibling("strong")
        expected = output_element.find_next_sibling(string=True).text
        decoded_expected = decode_value(expected)
        try:
            explanation_element = output_element.find_next_sibling("strong")
            explanation = str(
                explanation_element.find_next_sibling(string=True).text
            ).strip()
        except Exception:
            explanation = None
        tests.append(
            runner.Test(
                arguments=decoded_arguments,
                expected=decoded_expected,
                explanation=explanation,
            )
        )
    return tests


class FuncDefVisitor(pycparser.c_ast.NodeVisitor):
    def __init__(self) -> None:
        """"""
        super().__init__()
        self.function_name = None

    def visit_FuncDef(self, node):
        """
        Parameters
        ----------
        node
        """
        # Should be the last function declaration ?
        self.function_name = node.decl.name


def get_function_name(boilerplate_c: str):
    """
    Parameters
    ----------
    boilerplate_c: str
        The boilerplace C code to parse

    Raises
    ------
    ValueError
    """
    parser = pycparser.CParser()
    parsed = parser.parse(boilerplate_c)
    visitor = FuncDefVisitor()
    visitor.visit(parsed)
    if visitor.function_name is None:
        raise ValueError("Could not find function name")
    return visitor.function_name

