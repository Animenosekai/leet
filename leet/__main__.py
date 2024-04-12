import argparse
import pathlib
import typing
import urllib.parse
from rich.console import Console
from rich.table import Table
console = Console()

from leet.config import get_config
from leet.tests import Tests
from leet.graphql.question import Question, QuestionRequest
from leet.graphql.today import TodayRequest
from leet.templates import QUESTION_MARKDOWN
from leet.runners import LANG_TO_RUNNER
from markdownify import markdownify

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

    return QUESTION_MARKDOWN.format(
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

def human_size(bytes, units=[' bytes','KB','MB','GB','TB', 'PB', 'EB']):
    """Returns a human readable string representation of bytes. Stolen from https://stackoverflow.com/a/43750422"""
    return str(bytes) + units[0] if bytes < 1024 else human_size(bytes>>10, units[1:])

def main(args: argparse.Namespace):
    """
    Parameters
    ----------
    args: Namespace
    """
    config = get_config()
    if args.action == "run":
        file = pathlib.Path(args.file)
        if file.is_dir():
            for f in file.iterdir():
                if f.is_file() and f.suffix in EXT_TO_LANG:
                    file = f
                    break
        if file.with_suffix(".toml").is_file():
            tests = Tests.from_file(file.with_suffix(".toml"))
        elif (file.parent / "tests.toml").is_file():
            tests = Tests.from_file(file.parent / "tests.toml")
        else:
            raise ValueError("No tests file found.")
        if args.language in LANG_TO_EXT:
            language = args.language
        elif tests.language in LANG_TO_EXT:
            language = tests.language
        elif file.suffix in EXT_TO_LANG:
            language = EXT_TO_LANG[file.suffix]
        else:
            language = config.download.language
        
        runner = LANG_TO_RUNNER[language]
        time, cpu, mem = runner.run(code=file.read_text(), function_name=tests.function, tests=tests.tests)

        table = Table(title="Performance Metrics")

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
            output = config.download.output / f"{question_temp.id}-{question_temp.slug}"
        else:
            output = pathlib.Path(args.output)
        if output.is_file():
            if args.language in LANG_TO_EXT:
                language = args.language
            elif output.suffix in EXT_TO_LANG:
                language = EXT_TO_LANG[output.suffix]
            else:
                language = config.download.language
            output = output.parent
        elif args.language in LANG_TO_EXT:
            language = args.language
        else:
            language = config.download.language
        if not language in LANG_TO_EXT:
            language = config.download.language
        # Get the question
        question = question_temp or QuestionRequest(titleSlug=problem)
        # Perform download actions
        if args.download_action in ("solutions", "all"):
            # Download solutions
            pass
        if args.download_action in ("problem", "all"):
            # Download problem
            markdown_output = output if output.is_file() else output / "README.md"
            markdown_output.parent.mkdir(parents=True, exist_ok=True)
            markdown_output.write_text(to_markdown(question=question))
        if args.download_action in ("boilerplate", "all"):
            # Download boilerplate
            if output.is_file():
                boilerplate_output = output
            else:
                boilerplate_output = (output / "solve").with_suffix(
                    LANG_TO_EXT[language]
                )
            boilerplate_output.parent.mkdir(parents=True, exist_ok=True)
            boilerplate_output.write_text(
                boilerplate(question=question, language=language)
            )
        if args.download_action in ("tests", "all"):
            # Download tests
            pass


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

    def prepare_download_parser(parser: argparse.ArgumentParser):
        """
        Parameters
        ----------
        parser: ArgumentParser
        """
        parser.add_argument("problem", type=str, help="The problem URL or slug.")
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

