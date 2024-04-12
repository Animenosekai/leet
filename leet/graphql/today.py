import dataclasses
import typing

from leet.graphql.request import Request, Response

@dataclasses.dataclass
class Today(Response):
    slug: str

    @classmethod
    def morph(cls, data: dict[str, typing.Any]) -> "Today":
        return cls(slug=data["activeDailyCodingChallengeQuestion"]["question"]["titleSlug"])

TodayRequest = Request[Today](
    query="""
    query questionOfToday {
        activeDailyCodingChallengeQuestion {
            question {
            titleSlug
            }
        }
    }
    """,
    operation_name="questionOfToday",
    response=Today,
)
