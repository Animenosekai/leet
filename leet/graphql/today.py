"""Today's question query and response models."""

from __future__ import annotations

import dataclasses
import typing

from typing_extensions import override

from leet.graphql.request import Request, Response


@dataclasses.dataclass
class Today(Response):
    """The question of today."""

    slug: str

    @classmethod
    @override
    def morph(cls, data: dict[str, typing.Any]) -> Today:
        """
        Morph data into a Today object.

        Parameters
        ----------
        data: dict[str, typing.Any]
            The data to morph.

        Returns
        -------
        Today
            The morphed Today object.
        """
        return cls(
            slug=data["activeDailyCodingChallengeQuestion"]["question"]["titleSlug"],
        )


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
