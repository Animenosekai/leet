"""Module containing tools for handling and extracting tests."""

from __future__ import annotations

import dataclasses
import json
import pathlib
import re
import typing

import bs4
import pycparser  # pyright: ignore[reportMissingTypeStubs]
import pycparser.c_ast  # pyright: ignore[reportMissingTypeStubs]
import toml

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    import toml as tomllib  # type: ignore[no-redef]

from leet import runner


def _dict_factory() -> dict[str, str]:
    return {}


def _tests_factory() -> list[runner.Test]:
    return []


@dataclasses.dataclass
class Tests:
    """A class representing a collection of tests for a problem."""

    function: dict[str, str] = dataclasses.field(default_factory=_dict_factory)
    language: str | None = None
    tests: list[runner.Test] = dataclasses.field(default_factory=_tests_factory)

    @classmethod
    def from_file(cls, file: pathlib.Path) -> Tests:
        """
        Create a Tests object from a file.

        Parameters
        ----------
        cls
        file: pathlib.Path
            The path to the file to read.

        Returns
        -------
        Tests
        """
        content = typing.cast(
            dict[str, typing.Any],
            tomllib.loads(pathlib.Path(file).read_text()),  # pyright: ignore[reportUnknownMemberType]
        )
        func: typing.Any = content.get("function", {})
        if isinstance(func, str):
            func = {"*": func}
        return cls(
            function=typing.cast(dict[str, str], func or {}),
            language=typing.cast(str | None, content.get("language", None)),
            tests=[
                runner.Test(**typing.cast(dict[str, typing.Any], test))
                for test in typing.cast(
                    list[typing.Any],
                    content.get("tests", []),
                )
            ],
        )

    def to_dict(self) -> dict[str, typing.Any]:
        """
        Convert the tests to a dictionary.

        Returns
        -------
        dict[str, typing.Any]
        """
        return {
            "function": self.function,
            "language": self.language,
            "tests": [test.to_dict() for test in self.tests],
        }

    def dumps(self) -> str:
        """
        Dump the tests into a TOML string.

        Parameters
        ----------
        self

        Returns
        -------
        str
        """
        return toml.dumps(self.to_dict())


def decode_value(content: str) -> typing.Any:  # noqa: ANN401
    """
    Decode a string value into a Python object.

    Parameters
    ----------
    content: str
        The content to decode

    Returns
    -------
    typing.Any
        The decoded content
    """
    content = str(content).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return content


def extract_tests(html_content: str) -> list[runner.Test]:  # noqa: PLR0912, PLR0915
    """
    Extract tests from the problem description HTML.

    Parameters
    ----------
    html_content: str
        The html_content HTML

    Returns
    -------
    list[runner.Test]
    """
    tests_list: list[runner.Test] = []
    soup: typing.Any = bs4.BeautifulSoup(html_content, "html.parser")

    # Clean up non-breaking spaces and other weird whitespace
    for text_node in soup.find_all(string=True):
        if isinstance(text_node, bs4.NavigableString):
            new_text = text_node.replace("\xa0", " ").replace("\r\n", "\n")
            text_node.replace_with(new_text)

    # Find all elements that might be example markers
    # We look for tags that start with "Example \d+"
    # and we take the most specific one (the one with no children matching the same)
    markers: list[bs4.Tag] = []
    for tag in soup.find_all(["strong", "b", "p", "div", "span"]):
        text = tag.get_text().strip()
        if re.match(r"^Example \d+:?$", text, re.IGNORECASE):
            # Check if any child matches the same
            has_child_marker = False
            for child in tag.find_all(
                ["strong", "b", "p", "div", "span"],
                recursive=True,
            ):
                if re.match(
                    r"^Example \d+:?$",
                    child.get_text().strip(),
                    re.IGNORECASE,
                ):
                    has_child_marker = True
                    break
            if not has_child_marker:
                markers.append(tag)

    for marker in markers:
        # The content could be in a following <pre> or just in the following siblings
        content = ""

        # Try finding a <pre> tag nearby FIRST as it's the most common and structured
        # Also look for div with class example-block
        container = marker.find_next(["pre", "div", "blockquote"])
        if container and (
            container.name == "pre"
            or (
                container.name == "div"
                and any("example" in str(c) for c in container.get("class", []))
            )
        ):
            content = container.get_text(separator=" ")
        else:
            # Fallback: Gather text from siblings until the next example or a horizontal rule or end
            parts: list[str] = []
            curr = marker.next_sibling
            if not curr and marker.parent:
                curr = marker.parent.next_sibling

            while curr:
                if isinstance(curr, bs4.Tag):
                    if re.search(
                        r"^Example \d+:",
                        curr.get_text().strip(),
                        re.IGNORECASE,
                    ):
                        break
                    if curr.name == "hr":
                        break
                    parts.append(curr.get_text(separator=" "))
                elif isinstance(curr, bs4.NavigableString):
                    parts.append(str(curr))
                curr = curr.next_sibling
            content = " ".join(parts)

        # Clean up the content
        content = content.replace("\xa0", " ")
        # Remove zero-width spaces and other invisible characters
        for char in ["\u200b", "\u200c", "\u200d", "\ufeff"]:
            content = content.replace(char, "")
        content = re.sub(r"\s+", " ", content).strip()

        if "Input:" not in content or "Output:" not in content:
            continue

        # Extract Input, Output, and Explanation
        # Using more flexible regexes
        input_match = re.search(
            r"Input:\s*(.*?)\s*Output:",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        output_match = re.search(
            r"Output:\s*(.*?)\s*(?=Explanation:|$)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        explanation_match = re.search(
            r"Explanation:\s*(.*)",
            content,
            re.DOTALL | re.IGNORECASE,
        )

        if not input_match or not output_match:
            continue

        args_str = input_match.group(1).strip()
        expected_str = output_match.group(1).strip()
        explanation = explanation_match.group(1).strip() if explanation_match else None

        # Parse arguments
        decoded_arguments: dict[str, typing.Any] = {}
        # Match pattern: key = value
        # value ends at next key=, or end of string, or (common in LeetCode) a comma followed by key=
        arg_matches = list(
            re.finditer(
                r"([a-zA-Z_]\w*)\s*=\s*(.*?)(?=\s*,\s*[a-zA-Z_]\w*\s*=|(?:\n|\r\n)\s*[a-zA-Z_]\w*\s*=|$)",
                args_str,
                re.DOTALL,
            ),
        )

        if arg_matches:
            for m in arg_matches:
                k = m.group(1).strip()
                v = m.group(2).strip()
                if v.endswith(","):
                    v = v[:-1].strip()
                decoded_arguments[k] = decode_value(v)
        else:
            # Fallback for single argument or weird format
            decoded_arguments["arg"] = decode_value(args_str)

        tests_list.append(
            runner.Test(
                arguments=decoded_arguments,
                expected=decode_value(expected_str),
                explanation=explanation,
            ),
        )

    return tests_list


class FuncDefVisitor(pycparser.c_ast.NodeVisitor):  # pyright: ignore[reportMissingTypeStubs]
    """Visitor that finds function definitions in C code."""

    def __init__(self) -> None:
        """Initialize the visitor."""
        super().__init__()
        self.function_name: str | None = None

    def visit_func_def(self, node: pycparser.c_ast.FuncDef) -> None:
        """
        Visit a function definition node.

        Parameters
        ----------
        node: pycparser.c_ast.FuncDef
            The function definition node.
        """
        # Should be the last function declaration ?
        self.function_name = str(node.decl.name)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]

    visit_FuncDef = visit_func_def


def get_function_name(boilerplate_c: str) -> str:
    """
    Get the function name from the C boilerplate code.

    Parameters
    ----------
    boilerplate_c: str
        The boilerplace C code to parse

    Returns
    -------
    str
        The name of the function.

    Raises
    ------
    ValueError
    """
    parser = pycparser.CParser()
    parsed = parser.parse(boilerplate_c)
    visitor = FuncDefVisitor()
    visitor.visit(parsed)
    if visitor.function_name is None:
        msg = "Could not find function name"
        raise ValueError(msg)
    return visitor.function_name
