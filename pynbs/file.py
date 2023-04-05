__all__ = [
    "read",
    "new_file",
    "Parser",
    "Writer",
    "File",
    "Header",
    "Note",
    "Layer",
    "Instrument",
]


from dataclasses import dataclass
from io import BufferedReader, BufferedWriter
from struct import Struct
from typing import Generator, List, Tuple

CURRENT_NBS_VERSION = 5

BYTE = Struct("<B")
SHORT = Struct("<H")
SSHORT = Struct("<h")
INT = Struct("<I")


@dataclass
class Instrument:
    id: int
    name: str
    file: str
    pitch: int = 45
    press_key: bool = True


@dataclass
class Note:
    tick: int
    layer: int
    instrument: int
    key: int
    velocity: int = 100
    panning: int = 0
    pitch: int = 0


@dataclass
class Layer:
    id: int
    name: str = ""
    lock: bool = False
    volume: int = 100
    panning: int = 0


@dataclass
class Header:
    version: int = CURRENT_NBS_VERSION
    default_instruments: int = 16
    song_length: int = 0
    song_layers: int = 0
    song_name: str = ""
    song_author: str = ""
    original_author: str = ""
    description: str = ""
    tempo: float = 10.0
    auto_save: bool = False
    auto_save_duration: int = 10
    time_signature: int = 4
    minutes_spent: int = 0
    left_clicks: int = 0
    right_clicks: int = 0
    blocks_added: int = 0
    blocks_removed: int = 0
    song_origin: str = ""
    loop: bool = False
    max_loop_count: int = 0
    loop_start: int = 0


class File:
    def __init__(
        self,
        header: Header,
        notes: List[Note],
        layers: List[Layer],
        instruments: List[Instrument],
    ) -> None:
        self.header = header
        self.notes = notes
        self.layers = layers
        self.instruments = instruments

    def update_header(self, version: int) -> None:
        self.header.version = version
        if self.notes:
            self.header.song_length = self.notes[-1].tick
        self.header.song_layers = len(self.layers)

    def save(self, filename: str, version: int = CURRENT_NBS_VERSION) -> None:
        self.update_header(version)
        with open(filename, "wb") as fileobj:
            Writer(fileobj).encode_file(self, version)

    def __iter__(self) -> Generator[Tuple[int, List[Note]], None, None]:
        if not self.notes:
            return
        chord: List[Note] = []
        current_tick = self.notes[0].tick

        for note in sorted(self.notes, key=lambda n: n.tick):
            if note.tick == current_tick:
                chord.append(note)
            else:
                chord.sort(key=lambda n: n.layer)
                yield current_tick, chord
                current_tick, chord = note.tick, [note]
        yield current_tick, chord


class Parser:
    def __init__(self, fileobj: BufferedReader) -> None:
        self.fileobj = fileobj

    def read_file(self) -> File:
        header = self.parse_header()
        version = header.version
        return File(
            header,
            list(self.parse_notes(version)),
            list(self.parse_layers(header.song_layers, version)),
            list(self.parse_instruments(version)),
        )

    def read_numeric(self, fmt: Struct) -> int:
        return fmt.unpack(self.fileobj.read(fmt.size))[0]

    def read_string(self) -> str:
        length: int = self.read_numeric(INT)
        return self.fileobj.read(length).decode(encoding="cp1252")

    def jump(self) -> Generator[int, None, None]:
        value = -1
        while True:
            jump: int = self.read_numeric(SHORT)
            if not jump:
                break
            value += jump
            yield value

    def parse_header(self) -> Header:
        song_length = self.read_numeric(SHORT)
        if song_length == 0:
            # A song length of 0 indicates the Open Note Block Studio format
            version = self.read_numeric(BYTE)
        else:
            version = 0

        return Header(
            version=version,
            default_instruments=self.read_numeric(BYTE) if version > 0 else 10,
            song_length=self.read_numeric(SHORT) if version >= 3 else song_length,
            song_layers=self.read_numeric(SHORT),
            song_name=self.read_string(),
            song_author=self.read_string(),
            original_author=self.read_string(),
            description=self.read_string(),
            tempo=self.read_numeric(SHORT) / 100.0,
            auto_save=self.read_numeric(BYTE) == 1,
            auto_save_duration=self.read_numeric(BYTE),
            time_signature=self.read_numeric(BYTE),
            minutes_spent=self.read_numeric(INT),
            left_clicks=self.read_numeric(INT),
            right_clicks=self.read_numeric(INT),
            blocks_added=self.read_numeric(INT),
            blocks_removed=self.read_numeric(INT),
            song_origin=self.read_string(),
            loop=self.read_numeric(BYTE) == 1 if version >= 4 else False,
            max_loop_count=self.read_numeric(BYTE) if version >= 4 else 0,
            loop_start=self.read_numeric(SHORT) if version >= 4 else 0,
        )

    def parse_notes(self, version: int) -> Generator[Note, None, None]:
        for current_tick in self.jump():
            for current_layer in self.jump():
                instrument = self.read_numeric(BYTE)
                key = self.read_numeric(BYTE)
                velocity = self.read_numeric(BYTE) if version >= 4 else 100
                panning = self.read_numeric(BYTE) - 100 if version >= 4 else 0
                pitch = self.read_numeric(SSHORT) if version >= 4 else 0
                yield Note(
                    current_tick,
                    current_layer,
                    instrument,
                    key,
                    velocity,
                    panning,
                    pitch,
                )

    def parse_layers(
        self,
        layers_count: int,
        version: int,
    ) -> Generator[Layer, None, None]:
        for i in range(layers_count):
            name = self.read_string()
            lock = self.read_numeric(BYTE) == 1 if version >= 4 else False
            volume = self.read_numeric(BYTE)
            panning = self.read_numeric(BYTE) - 100 if version >= 2 else 0
            yield Layer(i, name, lock, volume, panning)

    def parse_instruments(self, version: int) -> Generator[Instrument, None, None]:
        for i in range(self.read_numeric(BYTE)):
            name = self.read_string()
            sound_file = self.read_string()
            pitch = self.read_numeric(BYTE)
            press_key = self.read_numeric(BYTE) == 1
            yield Instrument(i, name, sound_file, pitch, press_key)


class Writer:
    def __init__(self, fileobj: BufferedWriter) -> None:
        self.fileobj = fileobj

    def encode_file(self, nbs_file: File, version: int) -> None:
        self.write_header(nbs_file, version)
        self.write_notes(nbs_file, version)
        self.write_layers(nbs_file, version)
        self.write_instruments(nbs_file, version)

    def encode_numeric(self, fmt: Struct, value: int) -> None:
        self.fileobj.write(fmt.pack(value))

    def encode_string(self, value: str) -> None:
        self.encode_numeric(INT, len(value))
        self.fileobj.write(value.encode(encoding="cp1252"))

    def write_header(self, nbs_file: File, version: int) -> None:
        header = nbs_file.header

        if version > 0:
            self.encode_numeric(SHORT, 0)
            self.encode_numeric(BYTE, version)
            self.encode_numeric(BYTE, header.default_instruments)
        else:
            self.encode_numeric(SHORT, header.song_length)
        if version >= 3:
            self.encode_numeric(SHORT, header.song_length)
        self.encode_numeric(SHORT, header.song_layers)
        self.encode_string(header.song_name)
        self.encode_string(header.song_author)
        self.encode_string(header.original_author)
        self.encode_string(header.description)

        self.encode_numeric(SHORT, int(header.tempo * 100))
        self.encode_numeric(BYTE, int(header.auto_save))
        self.encode_numeric(BYTE, header.auto_save_duration)
        self.encode_numeric(BYTE, header.time_signature)

        self.encode_numeric(INT, header.minutes_spent)
        self.encode_numeric(INT, header.left_clicks)
        self.encode_numeric(INT, header.right_clicks)
        self.encode_numeric(INT, header.blocks_added)
        self.encode_numeric(INT, header.blocks_removed)
        self.encode_string(header.song_origin)

        if version >= 4:
            self.encode_numeric(BYTE, int(header.loop))
            self.encode_numeric(BYTE, header.max_loop_count)
            self.encode_numeric(SHORT, header.loop_start)

    def write_notes(self, nbs_file: File, version: int) -> None:
        current_tick = -1

        for tick, chord in nbs_file:
            self.encode_numeric(SHORT, tick - current_tick)
            current_tick = tick
            current_layer = -1

            for note in chord:
                self.encode_numeric(SHORT, note.layer - current_layer)
                current_layer = note.layer
                self.encode_numeric(BYTE, note.instrument)
                self.encode_numeric(BYTE, note.key)
                if version >= 4:
                    self.encode_numeric(BYTE, note.velocity)
                    self.encode_numeric(BYTE, note.panning + 100)
                    self.encode_numeric(SSHORT, note.pitch)

            self.encode_numeric(SHORT, 0)
        self.encode_numeric(SHORT, 0)

    def write_layers(self, nbs_file: File, version: int) -> None:
        for layer in nbs_file.layers:
            self.encode_string(layer.name)
            if version >= 4:
                self.encode_numeric(BYTE, int(layer.lock))
            self.encode_numeric(BYTE, layer.volume)
            if version >= 2:
                self.encode_numeric(BYTE, layer.panning + 100)

    def write_instruments(self, nbs_file: File, version: int) -> None:
        self.encode_numeric(BYTE, len(nbs_file.instruments))
        for instrument in nbs_file.instruments:
            self.encode_string(instrument.name)
            self.encode_string(instrument.file)
            self.encode_numeric(BYTE, instrument.pitch)
            self.encode_numeric(BYTE, int(instrument.press_key))


def read(filename: str) -> File:
    with open(filename, "rb") as fileobj:
        return Parser(fileobj).read_file()


def new_file(**header) -> File:
    return File(Header(**header), [], [Layer(0, "", False, 100, 0)], [])
