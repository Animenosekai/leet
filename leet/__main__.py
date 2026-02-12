"""The main entrypoint for the leet package."""

from __future__ import annotations

import argparse
import contextlib
import pathlib
import re
import sys
import urllib.parse

import pycparser  # pyright: ignore[reportMissingTypeStubs]
import rich.console
import rich.table
from markdownify import markdownify

from leet import config, runners, templates, tests
from leet.graphql.question import Question, QuestionRequest
from leet.graphql.today import TodayRequest

console = rich.console.Console()
LANG_TO_EXT = {
    "python3": ".py",
    "javascript": ".js",
    "java": ".java",
    "cpp": ".cpp",
    "c": ".c",
    "rust": ".rs",
    "go": ".go",
    "kotlin": ".kt",
    "swift": ".swift",
    "typescript": ".ts",
    "ruby": ".rb",
    "php": ".php",
    "csharp": ".cs",
    "objective-c": ".m",
    "scala": ".scala",
}
EXT_TO_LANG = {v: k for k, v in LANG_TO_EXT.items()}
URL_PATH_PROBLEMS_INDEX = 1
URL_PATH_SLUG_INDEX = 2
BYTES_PER_KB = 1024


def to_markdown(question: Question) -> str:
    """
    Convert a Question object to a markdown string.

    Parameters
    ----------
    question: Question
        The question to convert.

    Returns
    -------
    str
    """
    content = question.content.replace("&nbsp;", "")
    markdown_content = markdownify(content).strip()
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

    def markdown_list(content: list[str]) -> str:
        """
        Create a markdown list from a list of strings.

        Parameters
        ----------
        content: list[str]
            The list of strings to convert.
        """
        return "- " + "\n- ".join(content)

    def markdown_topic_link(topic: str, tag: str) -> str:
        """
        Create a markdown link to a topic.

        Parameters
        ----------
        topic: str
            The topic name.
        tag: str
            The topic slug.
        """
        return (
            f"[{topic}](https://leetcode.com/problemset/all-code-essentials/"
            f"?topicSlugs={tag}&page=1)"
        )

    def markdown_question_link(question_title: str, slug: str) -> str:
        """
        Create a markdown link to a question.

        Parameters
        ----------
        question_title: str
            The question title.
        slug: str
            The question slug.
        """
        return f"[{question_title}](https://leetcode.com/problems/{slug}/)"

    return templates.QUESTION_MARKDOWN.format(
        id=question.id,
        slug=question.slug,
        difficulty=question.difficulty.name,
        likes=question.likes,
        dislikes=question.dislikes,
        category=question.category.name,
        title=question.title,
        content=markdown_content,
        topics=markdown_list(
            [markdown_topic_link(key, value) for key, value in question.topics.items()],
        ),
        similar_questions=markdown_list(
            [
                markdown_question_link(key, value)
                for key, value in question.similar_questions.items()
            ],
        ),
        total_accepted=question.stats.total_accepted,
        total_submissions=question.stats.total_submissions,
        acceptance_rate=round(question.stats.acceptance_rate * 100, 2),
    )


def boilerplate(question: Question, language: str) -> str:
    """
    Return the boilerplate code for the given question and language.

    Parameters
    ----------
    question: Question
        The question to get the boilerplate for.
    language: str
        The language to get the boilerplate for.

    Returns
    -------
    str
    """
    return question.code_snippets[language]


def get_slug(url: str) -> str:
    """
    Extract the slug from the given URL.

    Example
    -------
    >>> get_slug("https://leetcode.com/problems/two-sum/")
    "two-sum"
    >>> get_slug("two-sum")
    "two-sum"
    >>> get_slug("today")
    "two-sum"
    >>> get_slug("daily")
    "two-sum"

    Parameters
    ----------
    url: str
        The URL or slug to extract from.

    Returns
    -------
    str

    Raises
    ------
    ValueError
        If the slug cannot be extracted.
    """

    def raise_msg(url_to_raise: str) -> None:
        msg = f"Couldn't get slug from URL: '{url_to_raise}'"
        raise ValueError(msg)

    if url in ["today", "daily"]:
        return TodayRequest().slug
    try:
        path = urllib.parse.urlparse(url).path.split("/")
        if (
            path[URL_PATH_PROBLEMS_INDEX] == "problems"
            and len(path) > URL_PATH_SLUG_INDEX
        ):
            return path[URL_PATH_SLUG_INDEX]
        raise_msg(url)
    except (ValueError, IndexError, AttributeError):
        pass
    return url


def human_size(num_bytes: int, units: list[str] | None = None) -> str:
    """
    Return a human readable string representation of bytes.

    Stolen from https://stackoverflow.com/a/43750422

    Parameters
    ----------
    num_bytes: int
        The number of bytes to convert.
    units: list[str] | None, default = None
        The units to use.

    Returns
    -------
    str
    """
    if units is None:
        units = [" bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    return (
        str(num_bytes) + units[0]
        if num_bytes < BYTES_PER_KB
        else human_size(num_bytes >> 10, units[1:])
    )


def fallback_function_from_slug(slug: str) -> str:
    """
    Return a fallback function name from the given slug.

    Parameters
    ----------
    slug: str
        The slug to convert.

    Returns
    -------
    str
    """
    splitted = slug.split("-")
    return splitted[0] + "".join(word.capitalize() for word in splitted[1:])


def resolve_run_file(args_file: str) -> pathlib.Path:
    """Resolve the file to run."""
    file = pathlib.Path(args_file)
    if file.is_dir():
        for f in file.iterdir():
            if f.is_file() and f.suffix in EXT_TO_LANG:
                return f
    return file


def resolve_tests(file: pathlib.Path) -> tests.Tests:
    """Resolve the tests content."""
    if file.with_suffix(".toml").is_file():
        return tests.Tests.from_file(file.with_suffix(".toml"))
    if (file.parent / "tests.toml").is_file():
        return tests.Tests.from_file(file.parent / "tests.toml")
    msg = "No tests file found."
    raise ValueError(msg)


def resolve_language(
    args_language: str | None,
    tests_language: str | None,
    file_suffix: str,
    default_language: str,
) -> str:
    """Resolve the language to use."""
    if args_language in LANG_TO_EXT:
        return args_language
    if tests_language in LANG_TO_EXT:
        return tests_language
    if file_suffix in EXT_TO_LANG:
        return EXT_TO_LANG[file_suffix]
    return default_language


def resolve_function_name(
    tests_function: dict[str, str],
    language: str,
    file_parent_stem: str,
) -> str:
    """Resolve the function name to use."""
    if language in tests_function:
        return tests_function[language]
    if "*" in tests_function:
        return tests_function["*"]
    slug = file_parent_stem
    num, _, rem = slug.partition("-")
    if num.isdigit():
        slug = rem
    return fallback_function_from_slug(slug)


def handle_run(args: argparse.Namespace, config_content: config.Config) -> None:
    """
    Handle the run action.

    Parameters
    ----------
    args: argparse.Namespace
        The parsed arguments.
    config_content: config.Config
        The configuration content.
    """
    file = resolve_run_file(args.file)
    tests_content = resolve_tests(file)
    language = resolve_language(
        args.language,
        tests_content.language,
        file.suffix,
        config_content.download.language,
    )
    runner = runners.LANG_TO_RUNNER[language]
    function_name = resolve_function_name(
        tests_content.function,
        language,
        file.parent.stem,
    )

    if args.dry:
        run_id, created = runner.create_file(
            code=file.read_text(),
            function_name=function_name,
            tests=tests_content.tests,
        )
        if str(args.output) != "-":
            output = args.output or file.with_suffix(
                f".test-{run_id}" + file.suffix,
            )
            output.write_text(created)
        else:
            console.print(created)
    else:
        res_time, res_cpu, res_mem = runner.run(
            code=file.read_text(),
            function_name=function_name,
            tests=tests_content.tests,
        )
        table = rich.table.Table(title="Performance Metrics")
        table.add_column("Runtime")
        table.add_column("CPU Usage")
        table.add_column("Memory")
        table.add_row(
            f"{round(res_time, 2)}ms",
            f"{round(res_cpu, 2)}%",
            human_size(int(res_mem)),
        )
        console.print(table)


def resolve_download_output(
    args_output: str | pathlib.Path | None,
    problem: str,
    config_content: config.Config,
) -> tuple[pathlib.Path, Question | None]:
    """Resolve the download output path."""
    if args_output is None:
        question_temp = QuestionRequest(titleSlug=problem)
        output = (
            config_content.download.output / f"{question_temp.id}-{question_temp.slug}"
        )
        return output, question_temp
    return pathlib.Path(args_output), None


def resolve_download_language(
    output: pathlib.Path,
    args_language: str | None,
    default_language: str,
) -> tuple[str, pathlib.Path]:
    """Resolve the download language and output directory."""
    language = default_language
    if output.is_file():
        if args_language in LANG_TO_EXT:
            language = args_language
        elif output.suffix in EXT_TO_LANG:
            language = EXT_TO_LANG[output.suffix]
        output = output.parent
    elif args_language in LANG_TO_EXT:
        language = args_language
    return language, output


def handle_download_problem(
    question: Question,
    output: pathlib.Path,
) -> None:
    """Handle the problem download."""
    created = to_markdown(question=question)
    if str(output) != "-":
        markdown_output = output if output.is_file() else output / "README.md"
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(created)
    else:
        console.print(created)


def handle_download_boilerplate(
    question: Question,
    language: str,
    output: pathlib.Path,
) -> None:
    """Handle the boilerplate download."""
    created = boilerplate(question=question, language=language)
    if str(output) != "-":
        if output.is_file():
            boilerplate_output = output
        else:
            boilerplate_output = (output / "solve").with_suffix(
                LANG_TO_EXT[language],
            )
        boilerplate_output.parent.mkdir(parents=True, exist_ok=True)
        boilerplate_output.write_text(created)
    else:
        console.print(created)


def handle_download_tests(
    question: Question,
    language: str,
    output: pathlib.Path,
) -> None:
    """Handle the tests download."""
    extracted_tests = tests.extract_tests(question.content)
    try:
        function_name = tests.get_function_name(question.code_snippets["c"])
    except (ValueError, KeyError, AttributeError, pycparser.c_parser.ParseError):
        function_name = fallback_function_from_slug(question.slug)

    function_content = {"*": function_name}
    with contextlib.suppress(Exception):
        function_content[language] = runners.LANG_TO_RUNNER[
            language
        ].function_location_from_name(
            function_name,
            question.code_snippets[language],
        )
    created = tests.Tests(
        function=function_content,
        language=language,
        tests=extracted_tests,
    ).dumps()
    if str(output) != "-":
        tests_output = output if output.is_file() else output / "tests.toml"
        tests_output.parent.mkdir(parents=True, exist_ok=True)
        tests_output.write_text(created)
    else:
        console.print(created)


def handle_download(
    args: argparse.Namespace,
    config_content: config.Config,
) -> None:
    """
    Handle the download action.

    Parameters
    ----------
    args: argparse.Namespace
        The parsed arguments.
    config_content: config.Config
        The configuration content.
    """
    if not args.download_action:
        args.download_action = "all"
    if not args.problem:
        args.problem = "today"

    problem = get_slug(args.problem)
    output, question_temp = resolve_download_output(
        args.output,
        problem,
        config_content,
    )
    language, output = resolve_download_language(
        output,
        args.language,
        config_content.download.language,
    )

    # Get the question
    question = question_temp or QuestionRequest(titleSlug=problem)

    # Perform download actions
    if args.download_action in ("solutions", "all"):
        # Download solutions
        pass
    if args.download_action in ("problem", "all"):
        handle_download_problem(question, output)
    if args.download_action in ("boilerplate", "all"):
        handle_download_boilerplate(question, language, output)
    if args.download_action in ("tests", "all"):
        handle_download_tests(question, language, output)


def main(args: argparse.Namespace) -> None:
    """
    Run the main logic.

    Parameters
    ----------
    args: argparse.Namespace
        The parsed arguments.
    """
    config_content = config.get_config()
    if args.action == "run":
        handle_run(args, config_content)
    elif args.action == "download":
        handle_download(args, config_content)


def prepare_parser(parser: argparse.ArgumentParser) -> None:
    """
    Prepare the argument parser.

    Parameters
    ----------
    parser: argparse.ArgumentParser
        The parser to prepare.
    """
    subparsers = parser.add_subparsers(dest="action")
    # Run Action
    run_parser = subparsers.add_parser(
        "run",
        description="Run a file using the same environment as on LeetCode.",
    )
    # Download Action
    download_parser = subparsers.add_parser(
        "download",
        description="Download a problem.",
    )
    download_subparsers = download_parser.add_subparsers(
        dest="download_action",
        required=False,
    )
    download_all_parser = download_subparsers.add_parser(
        "all",
        description="Download all resources for the problem.",
    )
    download_solutions_parser = download_subparsers.add_parser(
        "solutions",
        description="Download solutions for a given problem.",
    )
    download_problem_parser = download_subparsers.add_parser(
        "problem",
        description="Download the problem.",
    )
    download_boilerplate_parser = download_subparsers.add_parser(
        "boilerplate",
        description="Download the boilerplate code to start writing the solution.",
    )
    download_tests_parser = download_subparsers.add_parser(
        "tests",
        description="Download the tests for the problem.",
    )

    def prepare_run_parser(parser: argparse.ArgumentParser) -> None:
        """
        Prepare the run parser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            The parser to prepare.
        """
        parser.add_argument(
            "file",
            type=str,
            nargs="?",
            default=None,
            help="The file to run.",
        )
        parser.add_argument(
            "--language",
            "-l",
            type=str,
            default=None,
            help=(
                "The language to use. If not provided, inferred from the file "
                "extension."
            ),
        )
        parser.add_argument(
            "--dry",
            action="store_true",
            help="Generates a file which can be ran to test the function.",
        )
        if "--dry" in sys.argv:
            parser.add_argument(
                "--output",
                action="store",
                help="The output file to write the test file to.",
                type=pathlib.Path,
            )

    def prepare_download_parser(parser: argparse.ArgumentParser) -> None:
        """
        Prepare the download parser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            The parser to prepare.
        """
        parser.add_argument(
            "problem",
            type=str,
            help="The problem URL or slug.",
            nargs="?",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=pathlib.Path,
            default=None,
            help="The output path.",
        )
        parser.add_argument(
            "--language",
            "-l",
            type=str,
            default=None,
            help=(
                "The language to use. If not provided, inferred from the file "
                "extension. If impossible, defaults to 'python3'."
            ),
        )

    def prepare_download_solutions_parser(parser: argparse.ArgumentParser) -> None:
        """
        Prepare the download solutions parser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            The parser to prepare.
        """
        parser.add_argument(
            "--limit",
            type=int,
            default=3,
            help="The limit of solutions to download.",
        )

    def prepare_download_problem_parser(parser: argparse.ArgumentParser) -> None:
        """
        Prepare the download problem parser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            The parser to prepare.
        """

    def prepare_download_boilerplate_parser(parser: argparse.ArgumentParser) -> None:
        """
        Prepare the download boilerplate parser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            The parser to prepare.
        """

    def prepare_download_tests_parser(parser: argparse.ArgumentParser) -> None:
        """
        Prepare the download tests parser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            The parser to prepare.
        """

    prepare_run_parser(run_parser)
    # Prepare Download
    prepare_download_parser(download_parser)
    prepare_download_parser(download_all_parser)
    prepare_download_parser(download_solutions_parser)
    prepare_download_parser(download_problem_parser)
    prepare_download_parser(download_boilerplate_parser)
    prepare_download_parser(download_tests_parser)
    # Prepare All
    prepare_download_boilerplate_parser(download_all_parser)
    prepare_download_problem_parser(download_all_parser)
    prepare_download_solutions_parser(download_all_parser)
    prepare_download_tests_parser(download_all_parser)
    # Prepare Specific
    prepare_download_boilerplate_parser(download_boilerplate_parser)
    prepare_download_problem_parser(download_problem_parser)
    prepare_download_solutions_parser(download_solutions_parser)
    prepare_download_tests_parser(download_tests_parser)


def entry() -> None:
    """Run the main entrypoint."""
    parser = argparse.ArgumentParser(
        prog="leet",
        description="Solve LeetCode problems with fun ⛑️",
    )
    prepare_parser(parser)
    args = parser.parse_args()
    main(args=args)


if __name__ == "__main__":
    entry()
