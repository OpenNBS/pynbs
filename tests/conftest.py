from pathlib import Path

from pytest_insta import Fmt


class FmtNbs(Fmt[bytes]):
    extension = ".nbs"

    def load(self, path: Path) -> bytes:
        return path.read_bytes()

    def dump(self, path: Path, value: bytes):
        path.write_bytes(value)
