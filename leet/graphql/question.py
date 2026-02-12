"""Question query and response models."""

from __future__ import annotations

import dataclasses
import enum
import json
import typing

from typing_extensions import override

from leet.graphql.request import Request, Response


class Difficulty(enum.Enum):
    """The difficulty level of a LeetCode question."""

    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

    @classmethod
    def from_title(cls, title: str) -> Difficulty:
        """
        Create a Difficulty object from a title.

        Parameters
        ----------
        title: str
            The title of the difficulty.

        Returns
        -------
        Difficulty
            The difficulty object.
        """
        return cls(str(title).upper())


class Category(enum.Enum):
    """The category of a LeetCode question."""

    ALGORITHMS = "algorithms"
    DATABASE = "database"
    SHELL = "shell"
    CONCURRENCY = "concurrency"
    JAVASCRIPT = "javascript"
    PANDAS = "pandas"
    UNKNOWN = "unknown"

    @classmethod
    def from_title(cls, title: str) -> Category:
        """
        Create a Category object from a title.

        Parameters
        ----------
        title: str
            The title of the category.

        Returns
        -------
        Category
            The category object.
        """
        try:
            return cls(str(title).lower())
        except ValueError:
            return cls.UNKNOWN


@dataclasses.dataclass
class Stats:
    """The statistics of a LeetCode question."""

    total_accepted: int
    total_submissions: int

    @classmethod
    def morph(cls, data: dict[str, typing.Any]) -> Stats:
        """
        Morph data into a Stats object.

        Parameters
        ----------
        data: dict[str, typing.Any]
            The data to morph.

        Returns
        -------
        Stats
            The morphed Stats object.
        """
        return cls(
            total_accepted=data["totalAcceptedRaw"],
            total_submissions=data["totalSubmissionRaw"],
        )

    @property
    def acceptance_rate(self) -> float:
        """Return the acceptance rate."""
        return self.total_accepted / self.total_submissions


@dataclasses.dataclass
class Question(Response):
    """A LeetCode question."""

    id: str
    title: str
    slug: str
    difficulty: Difficulty
    likes: int
    dislikes: int
    category: Category

    content: str

    code_snippets: dict[str, str]

    topics: dict[str, str]

    stats: Stats

    similar_questions: dict[str, str]

    @classmethod
    @override
    def morph(cls, data: dict[str, typing.Any]) -> Question:
        """
        Morph data into a Question object.

        Parameters
        ----------
        data: dict[str, typing.Any]
            The data to morph.

        Returns
        -------
        Question
            The morphed Question object.
        """
        return cls(
            id=data["question"]["questionId"],
            title=data["question"]["title"],
            slug=data["question"]["titleSlug"],
            difficulty=Difficulty.from_title(data["question"]["difficulty"]),
            likes=data["question"]["likes"],
            dislikes=data["question"]["dislikes"],
            category=Category.from_title(data["question"]["categoryTitle"]),
            content=data["question"]["content"],
            code_snippets={
                snippet["langSlug"]: snippet["code"]
                for snippet in data["question"]["codeSnippets"]
            },
            topics={tag["name"]: tag["slug"] for tag in data["question"]["topicTags"]},
            stats=Stats.morph(json.loads(data["question"]["stats"])),
            similar_questions={
                question["title"]: question["titleSlug"]
                for question in data["question"]["similarQuestionList"]
            },
        )


QuestionRequest = Request[Question](
    query="""
    query queryQuestion($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            # questionTitle
            questionId
            title
            titleSlug
            difficulty
            likes
            dislikes
            categoryTitle

            # questionContent
            content

            # questionEditorData
            codeSnippets {
                langSlug
                code
            }

            # singleQuestionTopicTags
            topicTags {
                name
                slug
            }

            # questionStats
            stats

            # SimilarQuestions
            similarQuestionList {
                title
                titleSlug
            }
        }
    }
    """,
    operation_name="queryQuestion",
    response=Question,
)
