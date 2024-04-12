import argparse
import pathlib
import sys
import typing
import urllib.parse

import rich.console
import rich.table
from leet import config, runners, templates, tests
from leet.graphql.question import Question, QuestionRequest
from leet.graphql.today import TodayRequest
from markdownify import markdownify

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


def to_markdown(question: Question):
    """
    Parameters
    ----------
    question: Question
    problem: str
    """
    markdown_content = markdownify(question.content).replace("\n\n", "\n").strip()

    def markdown_list(content: typing.List[str]):
        """
        Parameters
        ----------
        content: list
        """
        return "- " + "\n- ".join(content)

    def markdown_topic_link(topic: str, tag: str):
        """
        Parameters
        ----------
        topic: str
        tag: str
        """
        return f"[{topic}](https://leetcode.com/problemset/all-code-essentials/?topicSlugs={tag}&page=1)"

    def markdown_question_link(question: str, slug: str):
        """
        Parameters
        ----------
        question: str
        slug: str
        """
        return f"[{question}](https://leetcode.com/problems/{slug}/)"

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
            [markdown_topic_link(key, value) for key, value in question.topics.items()]
        ),
        similar_questions=markdown_list(
            [
                markdown_question_link(key, value)
                for key, value in question.similar_questions.items()
            ]
        ),
        total_accepted=question.stats.total_accepted,
        total_submissions=question.stats.total_submissions,
        acceptance_rate=round(question.stats.acceptance_rate * 100, 2),
    )


def boilerplate(question: Question, language: str):
    """
    Parameters
    ----------
    question: Question
    language: str
    """
    return question.code_snippets[language]


def get_slug(url: str):
    """
    Extracts the slug from the given URL.

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

    Returns
    -------
    str

    Raises
    ------
    ValueError
    """
    if url in ["today", "daily"]:
        return TodayRequest().slug
    try:
        path = urllib.parse.urlparse(url).path.split("/")
        if path[1] == "problems" and len(path) > 2:
            return path[2]
        raise ValueError(f"Couldn't get slug from URL: '{url}'")
    except Exception:
        pass
    return url


def human_size(bytes, units=[" bytes", "KB", "MB", "GB", "TB", "PB", "EB"]):
    """
    Returns a human readable string representation of bytes. Stolen from https://stackoverflow.com/a/43750422

    Parameters
    ----------
    bytes
    units
    """
    return str(bytes) + units[0] if bytes < 1024 else human_size(bytes >> 10, units[1:])


def fallback_function_from_slug(slug: str):
    """
    Parameters
    ----------
    slug: str
    """
    splitted = slug.split("-")
    return splitted[0] + "".join((word.capitalize() for word in splitted[1:]))


def main(args: argparse.Namespace):
    """
    Parameters
    ----------
    args: Namespace
    """
    config_content = config.get_config()
    if args.action == "run":
        file = pathlib.Path(args.file)
        if file.is_dir():
            for f in file.iterdir():
                if f.is_file() and f.suffix in EXT_TO_LANG:
                    file = f
                    break
        if file.with_suffix(".toml").is_file():
            tests_content = tests.Tests.from_file(file.with_suffix(".toml"))
        elif (file.parent / "tests.toml").is_file():
            tests_content = tests.Tests.from_file(file.parent / "tests.toml")
        else:
            raise ValueError("No tests file found.")
        if args.language in LANG_TO_EXT:
            language = args.language
        elif tests_content.language in LANG_TO_EXT:
            language = tests_content.language
        elif file.suffix in EXT_TO_LANG:
            language = EXT_TO_LANG[file.suffix]
        else:
            language = config_content.download.language
        runner = runners.LANG_TO_RUNNER[language]
        if language in tests_content.function:
            function_name = tests_content.function[language]
        elif "*" in tests_content.function:
            function_name = tests_content.function["*"]
        else:
            slug = file.parent.stem
            num, _, rem = slug.partition("-")
            if num.isdigit():
                slug = rem
            function_name = fallback_function_from_slug(slug)
        if args.dry:
            run_id, created = runner.create_file(
                code=file.read_text(),
                function_name=function_name,
                tests=tests_content.tests,
            )
            if str(args.output) != "-":
                output = args.output or file.with_suffix(f".test-{run_id}" + file.suffix)
                output.write_text(created)
            else:
                print(created)
        else:
            time, cpu, mem = runner.run(
                code=file.read_text(),
                function_name=function_name,
                tests=tests_content.tests,
            )
            table = rich.table.Table(title="Performance Metrics")
            table.add_column("Runtime")
            table.add_column("CPU Usage")
            table.add_column("Memory")
            table.add_row(f"{round(time, 2)}ms", f"{round(cpu, 2)}%", human_size(mem))
            console.print(table)
    elif args.action == "download":
        if not args.download_action:
            args.download_action = "all"
            args.problem = "today"
        # Validate inputs
        problem = get_slug(args.problem)
        print("Downloading problem:", problem)
        question_temp = None
        if args.output is None:
            question_temp = QuestionRequest(titleSlug=problem)
            output = (
                config_content.download.output
                / f"{question_temp.id}-{question_temp.slug}"
            )
        else:
            output = pathlib.Path(args.output)
        if output.is_file():
            if args.language in LANG_TO_EXT:
                language = args.language
            elif output.suffix in EXT_TO_LANG:
                language = EXT_TO_LANG[output.suffix]
            else:
                language = config_content.download.language
            output = output.parent
        elif args.language in LANG_TO_EXT:
            language = args.language
        else:
            language = config_content.download.language
        if not language in LANG_TO_EXT:
            language = config_content.download.language
        # Get the question
        question = question_temp or QuestionRequest(titleSlug=problem)
        # Perform download actions
        if args.download_action in ("solutions", "all"):
            # Download solutions
            pass
        if args.download_action in ("problem", "all"):
            # Download problem
            created = to_markdown(question=question)
            if str(output) != "-":
                markdown_output = output if output.is_file() else output / "README.md"
                markdown_output.parent.mkdir(parents=True, exist_ok=True)
                markdown_output.write_text(created)
            else:
                print(created)
        if args.download_action in ("boilerplate", "all"):
            # Download boilerplate
            created = boilerplate(question=question, language=language)
            if str(output) != "-":
                if output.is_file():
                    boilerplate_output = output
                else:
                    boilerplate_output = (output / "solve").with_suffix(
                        LANG_TO_EXT[language]
                    )
                boilerplate_output.parent.mkdir(parents=True, exist_ok=True)
                boilerplate_output.write_text(created)
            else:
                print(created)
        if args.download_action in ("tests", "all"):
            # Download tests
            extracted_tests = tests.extract_tests(question.content)
            try:
                function_name = tests.get_function_name(question.code_snippets["c"])
            except Exception:
                function_name = fallback_function_from_slug(question.slug)
            function_content = {"*": function_name}
            try:
                function_content[language] = runners.LANG_TO_RUNNER[
                    language
                ].function_location_from_name(
                    function_name, question.code_snippets[language]
                )
            except Exception:
                pass
            created = tests.Tests(
                function=function_content, language=language, tests=extracted_tests
            ).dumps()
            if str(output) != "-":
                if output.is_file():
                    tests_output = output
                else:
                    tests_output = output / "tests.toml"
                tests_output.parent.mkdir(parents=True, exist_ok=True)
                tests_output.write_text(created)
            else:
                print(created)


def prepare_parser(parser: argparse.ArgumentParser):
    """
    Parameters
    ----------
    parser: ArgumentParser
    """
    subparsers = parser.add_subparsers(dest="action")
    # Run Action
    run_parser = subparsers.add_parser(
        "run", description="Run a file using the same environment as on LeetCode."
    )
    # Download Action
    download_parser = subparsers.add_parser(
        "download", description="Download a problem."
    )
    download_subparsers = download_parser.add_subparsers(
        dest="download_action", required=False
    )
    download_all_parser = download_subparsers.add_parser(
        "all", description="Download all resources for the problem."
    )
    download_solutions_parser = download_subparsers.add_parser(
        "solutions", description="Download solutions for a given problem."
    )
    download_problem_parser = download_subparsers.add_parser(
        "problem", description="Download the problem."
    )
    download_boilerplate_parser = download_subparsers.add_parser(
        "boilerplate",
        description="Download the boilerplate code to start writing the solution.",
    )
    download_tests_parser = download_subparsers.add_parser(
        "tests", description="Download the tests for the problem."
    )

    def prepare_run_parser(parser: argparse.ArgumentParser):
        """
        Parameters
        ----------
        parser: ArgumentParser
        """
        parser.add_argument(
            "file", type=str, nargs="?", default=None, help="The file to run."
        )
        parser.add_argument(
            "--language",
            "-l",
            type=str,
            default=None,
            help="The language to use. If not provided, inferred from the file extension.",
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

    def prepare_download_parser(parser: argparse.ArgumentParser):
        """
        Parameters
        ----------
        parser: ArgumentParser
        """
        parser.add_argument(
            "problem", type=str, help="The problem URL or slug.", nargs="?"
        )
        parser.add_argument(
            "--output", "-o", type=pathlib.Path, default=None, help="The output path."
        )
        parser.add_argument(
            "--language",
            "-l",
            type=str,
            default=None,
            help="The language to use. If not provided, inferred from the file extension. If impossible, defaults to 'python3'.",
        )

    def prepare_download_solutions_parser(parser: argparse.ArgumentParser):
        """
        Parameters
        ----------
        parser: ArgumentParser
        """
        pass
        parser.add_argument(
            "--limit", type=int, default=3, help="The limit of solutions to download."
        )

    def prepare_download_problem_parser(parser: argparse.ArgumentParser):
        """
        Parameters
        ----------
        parser: ArgumentParser
        """
        pass

    def prepare_download_boilerplate_parser(parser: argparse.ArgumentParser):
        """
        Parameters
        ----------
        parser: ArgumentParser
        """
        pass

    def prepare_download_tests_parser(parser: argparse.ArgumentParser):
        """
        Parameters
        ----------
        parser: ArgumentParser
        """
        pass

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


def entry():
    """The main entrypoint"""
    parser = argparse.ArgumentParser()
    prepare_parser(parser)
    args = parser.parse_args()
    main(args=args)


if __name__ == "__main__":
    entry()

