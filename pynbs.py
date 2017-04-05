
from struct import Struct
from collections import namedtuple


__all__ = ['read', 'Parser', 'File', 'Header', 'Note', 'Layer', 'Instrument']


BYTE = Struct('<b')
SHORT = Struct('<h')
INT = Struct('<i')


Note = namedtuple('Note', ['tick', 'layer', 'instrument', 'key'])
Layer = namedtuple('Layer', ['id', 'name', 'volume'])
Instrument = namedtuple('Instrument', ['id', 'name', 'file', 'pitch',
                                       'press_key'])


def read(filename):
    with open(filename, 'rb') as buff:
        return Parser(buff).read_file()


class Header(object):
    def __init__(self, headers):
        for key, value in headers:
            setattr(self, key, value)


class File(object):
    def __init__(self, header, notes, layers, instruments):
        self.header = header
        self.notes = notes
        self.layers = layers
        self.instruments = instruments

    def song(self):
        if not self.notes:
            return
        chord = []
        current_tick = self.notes[0].tick

        for note in self.notes:
            if note.tick == current_tick:
                chord.append(note)
            else:
                yield current_tick, chord
                current_tick, chord = note.tick, [note]


class Parser(object):
    def __init__(self, buff):
        self.buffer = buff

    def read_file(self):
        header = Header(self.parse_header().items())
        return File(header, list(self.parse_notes()),
                    list(self.parse_layers(header.song_layers)),
                    list(self.parse_instruments()))

    def read_numeric(self, fmt):
        return fmt.unpack(self.buffer.read(fmt.size))[0]

    def read_string(self):
        length = self.read_numeric(INT)
        return self.buffer.read(length).decode()

    def jump(self):
        value = -1
        while True:
            jump = self.read_numeric(SHORT)
            if not jump:
                break
            value += jump
            yield value

    def parse_header(self):
        return {
            'song_length':         self.read_numeric(SHORT),
            'song_layers':         self.read_numeric(SHORT),
            'song_name':           self.read_string(),
            'song_author':         self.read_string(),
            'original_author':     self.read_string(),
            'description':         self.read_string(),

            'tempo':               self.read_numeric(SHORT) / 100.0,
            'auto_save':           self.read_numeric(BYTE) == 1,
            'auto_save_duration':  self.read_numeric(BYTE),
            'time_signature':      '{}/4'.format(self.read_numeric(BYTE)),

            'minutes_spent':       self.read_numeric(INT),
            'left_clicks':         self.read_numeric(INT),
            'right_clicks':        self.read_numeric(INT),
            'blocks_added':        self.read_numeric(INT),
            'blocks_removed':      self.read_numeric(INT),
            'song_origin':         self.read_string(),
        }

    def parse_notes(self):
        for current_tick in self.jump():
            for current_layer in self.jump():
                yield Note(current_tick, current_layer,
                           self.read_numeric(BYTE), self.read_numeric(BYTE))

    def parse_layers(self, layers_count):
        for i in range(layers_count):
            yield Layer(i, self.read_string(), self.read_numeric(BYTE))

    def parse_instruments(self):
        for i in range(self.read_numeric(BYTE)):
            yield Instrument(i, self.read_string(), self.read_string(),
                             self.read_numeric(BYTE),
                             self.read_numeric(BYTE) == 1)
