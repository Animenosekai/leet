import enum
import dataclasses
import typing
import json

from leet.graphql.request import Request, Response

class Difficulty(enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

    @classmethod
    def from_title(cls, title: str) -> "Difficulty":
        return cls(str(title).upper())

class Category(enum.Enum):
    ALGORITHMS = "algorithms"
    DATABASE = "database"
    SHELL = "shell"
    CONCURRENCY = "concurrency"
    JAVASCRIPT = "javascript"
    PANDAS = "pandas"
    UNKNOWN = "unknown"

    @classmethod
    def from_title(cls, title: str) -> "Category":
        try:
            return cls(str(title).upper())
        except ValueError:
            return cls.UNKNOWN

@dataclasses.dataclass
class Stats:
    total_accepted: int
    total_submissions: int

    @classmethod
    def morph(cls, data: dict[str, typing.Any]) -> typing.Self:
        return cls(
            total_accepted=data["totalAcceptedRaw"],
            total_submissions=data["totalSubmissionRaw"]
        )
    
    @property
    def acceptance_rate(self) -> float:
        return self.total_accepted / self.total_submissions


@dataclasses.dataclass
class Question(Response):
    id: str
    title: str
    slug: str
    difficulty: Difficulty
    likes: int
    dislikes: int
    category: Category

    content: str

    code_snippets: typing.Dict[str, str]

    topics: typing.Dict[str, str]

    stats: Stats
    
    similar_questions: typing.Dict[str, str]

    @classmethod
    def morph(cls, data: dict[str, typing.Any]) -> typing.Self:
        return cls(
            id=data["question"]["questionId"],
            title=data["question"]["title"],
            slug=data["question"]["titleSlug"],
            difficulty=Difficulty.from_title(data["question"]["difficulty"]),
            likes=data["question"]["likes"],
            dislikes=data["question"]["dislikes"],
            category=Category.from_title(data["question"]["categoryTitle"]),
            content=data["question"]["content"],
            code_snippets={snippet["langSlug"]: snippet["code"] for snippet in data["question"]["codeSnippets"]},
            topics={tag["name"]: tag["slug"] for tag in data["question"]["topicTags"]},
            stats=Stats.morph(json.loads(data["question"]["stats"])),
            similar_questions={question["title"]: question["titleSlug"] for question in data["question"]["similarQuestionList"]}
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
