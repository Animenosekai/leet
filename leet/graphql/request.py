import dataclasses
import typing

import requests


class Response:
    @classmethod
    def morph(cls, data: dict[str, typing.Any]) -> typing.Self:
        """
        Parameters
        ----------
        cls
        data: dict

        Returns
        -------
        Self

        Raises
        ------
        NotImplementedError
        """
        return cls(**data)


T = typing.TypeVar("T", bound=Response)


@dataclasses.dataclass
class Request(typing.Generic[T]):
    query: str
    operation_name: str
    response: typing.Type[T]

    def request(self, variables: typing.Dict[str, typing.Any] | None = None, **kwargs) -> T:
        """
        Parameters
        ----------
        variables: dict

        Returns
        -------
        T
        """
        variables = variables or {}
        variables.update(kwargs)
        url = "https://leetcode.com/graphql"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        }
        data = {
            "query": self.query,
            "variables": variables,
            "operationName": self.operation_name,
        }
        response = requests.post(url, headers=headers, json=data)
        return self.response.morph(response.json()["data"])


    __call__ = request