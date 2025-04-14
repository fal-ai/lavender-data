from abc import ABC, abstractmethod
import urllib.parse
from typing_extensions import Self


class Storage(ABC):
    scheme: str

    @classmethod
    def get(cls, remote_path: str) -> Self:
        parsed = urllib.parse.urlparse(remote_path)
        scheme = parsed.scheme
        for subcls in cls.__subclasses__():
            if scheme == subcls.scheme:
                try:
                    return subcls()
                except ImportError as e:
                    raise ImportError(
                        f"Please install required dependencies for {subcls.__name__}"
                    ) from e
        raise ValueError(f"Invalid protocol: {parsed.scheme}")

    @abstractmethod
    def download(self, remote_path: str, local_path: str) -> None: ...

    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> None: ...

    @abstractmethod
    def list(self, remote_path: str) -> list[str]: ...
