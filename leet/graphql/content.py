"""Content query and response models."""

from __future__ import annotations

import dataclasses
import typing

from typing_extensions import override

from leet.graphql.request import Request, Response


@dataclasses.dataclass
class Content(Response):
    """The content of a LeetCode question."""

    content: str
    mysql_schemas: list[str]
    data_schemas: list[str]

    @classmethod
    @override
    def morph(cls, data: dict[str, typing.Any]) -> Content:
        """
        Morph data into a Content object.

        Parameters
        ----------
        data: dict[str, typing.Any]
            The data to morph.

        Returns
        -------
        typing.Self
            The morphed Content object.
        """
        return cls(
            content=data["question"]["content"],
            mysql_schemas=data["question"]["mysqlSchemas"],
            data_schemas=data["question"]["dataSchemas"],
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
