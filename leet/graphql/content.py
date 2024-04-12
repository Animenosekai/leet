import dataclasses
import typing

from leet.graphql.request import Request, Response

@dataclasses.dataclass
class Content(Response):
    content: str
    mysql_schemas: typing.List[str]
    data_schemas: typing.List[str]

    @classmethod
    def morph(cls, data: dict[str, typing.Any]) -> typing.Self:
        return cls(
            content=data["question"]["content"],
            mysql_schemas=data["question"]["mysqlSchemas"],
            data_schemas=data["question"]["dataSchemas"]
        )

ContentRequest = Request[Content](
    query="""
    query questionContent($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            content
            mysqlSchemas
            dataSchemas
        }
    }
    """,
    operation_name="questionContent",
    response=Content,
)
