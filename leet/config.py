"""Configuration for the leet package."""

from __future__ import annotations

import dataclasses
import pathlib
import typing

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    import toml as tomllib  # type: ignore[no-redef]

CONFIGURATION_FILE = pathlib.Path("leet.toml")


@dataclasses.dataclass
class DownloadConfiguration:
    """
    Download configuration.

    Parameters
    ----------
    language: str
        The default language to use for downloads.
    output: pathlib.Path
        The default output path for downloads.
    """

    language: str = "python3"
    output: pathlib.Path = dataclasses.field(default_factory=pathlib.Path)


@dataclasses.dataclass
class Config:
    """
    Global configuration.

    Parameters
    ----------
    download: DownloadConfiguration
        The download configuration.
    """

    download: DownloadConfiguration

    @classmethod
    def from_file(cls, file: pathlib.Path | None = None) -> Config:
        """
        Create a configuration from a file.

        Parameters
        ----------
        file: pathlib.Path | None
            The file to read the configuration from.

        Returns
        -------
        Config
            The configuration.
        """
        file = file or CONFIGURATION_FILE
        config = (
            typing.cast(
                dict[str, typing.Any],
                tomllib.loads(file.read_text()),  # pyright: ignore[reportUnknownMemberType]
            )
            if file.is_file()
            else {}
        )
        download = config.get("download", {})
        return cls(
            download=DownloadConfiguration(
                language=download.get("language", "python3"),
                output=pathlib.Path(download.get("output", pathlib.Path())),
            ),
        )


def get_config() -> Config:
    """
    Get the default values for the CLI.

    Returns
    -------
    Config
        The configuration.
    """
    return Config.from_file()
