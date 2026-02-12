"""GraphQL request and response handling."""

from __future__ import annotations

import dataclasses
import typing

import requests

DEFAULT_TIMEOUT = 10

R = typing.TypeVar("R", bound="Response")


class Response:
    """Base response class."""

    @classmethod
    def morph(cls: type[R], data: dict[str, typing.Any]) -> R:
        """
        Morph data into a response object.

        Parameters
        ----------
        data: dict[str, typing.Any]
            The data to morph.

        Returns
        -------
        R
            The morphed response object.
        """
        return cls(**data)


T = typing.TypeVar("T", bound=Response)


@dataclasses.dataclass
class Request(typing.Generic[T]):
    """
    GraphQL request.

    Parameters
    ----------
    query: str
        The query string.
    operation_name: str
        The operation name.
    response: type[T]
        The response type.
    """

    query: str
    operation_name: str
    response: type[T]

    def request(
        self,
        variables: dict[str, typing.Any] | None = None,
        **kwargs: typing.Any,  # noqa: ANN401
    ) -> T:
        """
        Perform the GraphQL request.

        Parameters
        ----------
        variables: dict[str, typing.Any] | None
            The variables to use.
        **kwargs: typing.Any
            Additional variables.

        Returns
        -------
        T
            The response object.
        """
        variables = variables or {}
        variables.update(kwargs)
        url = "https://leetcode.com/graphql"
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.3"
        )
        headers = {
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        }
        data = {
            "query": self.query,
            "variables": variables,
            "operationName": self.operation_name,
        }
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=DEFAULT_TIMEOUT,
        )
        return self.response.morph(response.json()["data"])

    __call__ = request
