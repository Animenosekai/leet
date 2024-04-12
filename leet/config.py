import dataclasses
import pathlib
import tomllib

CONFIGURATION_FILE = pathlib.Path("leet.toml")


@dataclasses.dataclass
class DownloadConfiguration:
    language: str = "python3"
    output: pathlib.Path = dataclasses.field(default_factory=pathlib.Path)


@dataclasses.dataclass
class Configuration:
    download: DownloadConfiguration

    @classmethod
    def from_file(cls, file: pathlib.Path | None = None) -> "Configuration":
        """
        Parameters
        ----------
        cls
        file: default = None

        Returns
        -------
        Configuration
        """
        file = file or CONFIGURATION_FILE
        if file.is_file():
            config = tomllib.loads(file.read_text())
        else:
            config = {}
        download = config.get("download", {})
        return cls(
            download=DownloadConfiguration(
                language=download.get("language", "python3"),
                output=pathlib.Path(download.get("output", pathlib.Path())),
            )
        )


def get_config():
    """
    Returns the default values for the CLI.

    Returns
    -------
    dict
    """
    return Configuration.from_file()

