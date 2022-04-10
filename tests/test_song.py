import os
from pathlib import Path

import pytest
from pytest_insta import SnapshotFixture

import pynbs


@pytest.mark.parametrize("filename", os.listdir("tests/resources"))
def test_notes(snapshot: SnapshotFixture, filename: str):
    f = pynbs.read(f"tests/resources/{filename}")
    data = "".join(f"{tick}: {[note.key for note in chord]}\n" for tick, chord in f)
    assert snapshot() == (
        f"{f.header.song_length = }\n"
        f"{f.header.description = }\n"
        f"{len(f.notes) = }\n"
        f"{len(f.layers) = }\n"
        f"{len(f.instruments) = }\n"
        f"{data}"
    )


def test_create(snapshot: SnapshotFixture, tmp_path: Path):
    f = pynbs.new_file(song_name="foo", song_author="bar")

    f.notes.extend(
        [
            pynbs.Note(tick=0, layer=0, instrument=0, key=45),
            pynbs.Note(tick=2, layer=0, instrument=0, key=45),
            pynbs.Note(tick=4, layer=0, instrument=0, key=45),
            pynbs.Note(tick=6, layer=0, instrument=0, key=45),
            pynbs.Note(tick=8, layer=0, instrument=0, key=45),
        ]
    )

    f.header.blocks_added = 9000

    f.save(tmp_path / "new.nbs")
    f.save(tmp_path / "old.nbs", version=0)

    new = (tmp_path / "new.nbs").read_bytes()
    old = (tmp_path / "old.nbs").read_bytes()
    assert new != old

    assert snapshot("new.nbs") == new
    assert snapshot("old.nbs") == old
