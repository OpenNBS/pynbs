from __future__ import print_function, division, absolute_import

try:
    from builtins import range
except ImportError:
    range = xrange

from struct import Struct
from collections import namedtuple


__all__ = ['read', 'new_file', 'Parser', 'Writer', 'File', 'Header',
           'Note', 'Layer', 'Instrument']

CURRENT_NBS_VERSION = 4

BYTE = Struct('<b')
SHORT = Struct('<h')
SSHORT = Struct('<H')
INT = Struct('<i')



Instrument = namedtuple('Instrument', ['id', 'name', 'file', 'pitch',
                                       'press_key'])


class Note(namedtuple('Note', ['tick', 'layer', 'instrument', 'key',
                      'velocity', 'panning', 'pitch'])):
    def __new__(cls, tick, layer, instrument, key, velocity=100,
               panning=0, pitch=0):
        return super().__new__(cls, tick, layer, instrument, key,
                               velocity, panning, pitch)

class Layer(namedtuple('Layer', ['id', 'name', 'lock', 'volume', 'panning'])):
    def __new__(cls, id, name="", lock=False, volume=100, panning=0):
        return super().__new__(cls, id, name, lock, volume, panning)


def read(filename):
    with open(filename, 'rb') as buff:
        return Parser(buff).read_file()


def new_file(**header):
    return File(Header(**header), [], [Layer(0, '', False, 100, 0)], [])


class Header(object):
    def __init__(self, **header):
        header_values = {
            'version':              header.get('version', CURRENT_NBS_VERSION),
            'default_instruments':  header.get('default_instruments', 16),
            'song_length':          header.get('song_length', 0),
            'song_layers':          header.get('song_layers', 0),
            'song_name':            header.get('song_name', ''),
            'song_author':          header.get('song_author', ''),
            'original_author':      header.get('original_author', ''),
            'description':          header.get('description', ''),

            'tempo':                header.get('tempo', 10.0),
            'auto_save':            header.get('auto_save', False),
            'auto_save_duration':   header.get('auto_save_duration', 10),
            'time_signature':       header.get('time_signature', 4),

            'minutes_spent':        header.get('minutes_spent', 0),
            'left_clicks':          header.get('left_clicks', 0),
            'right_clicks':         header.get('right_clicks', 0),
            'blocks_added':         header.get('blocks_added', 0),
            'blocks_removed':       header.get('blocks_removed', 0),
            'song_origin':          header.get('song_origin', ''),

            'loop':                 header.get('loop', False),
            'max_loop_count':       header.get('max_loop_count', 0),
            'loop_start':           header.get('loop_start', 0)
        }

        for key, value in header_values.items():
            setattr(self, key, value)


class File(object):
    def __init__(self, header, notes, layers, instruments):
        self.header = header
        self.notes = notes
        self.layers = layers
        self.instruments = instruments

    def update_header(self, version):
        self.header.version = version
        if self.notes:
            self.header.song_length = self.notes[-1].tick
        self.header.song_layers = len(self.layers)

    def save(self, filename, version=CURRENT_NBS_VERSION):
        self.update_header(version)
        with open(filename, 'wb') as buff:
            Writer(buff).encode_file(self, version)

    def __iter__(self):
        if not self.notes:
            return
        chord = []
        current_tick = self.notes[0].tick

        for note in sorted(self.notes, key=lambda n: n.tick):
            if note.tick == current_tick:
                chord.append(note)
            else:
                chord.sort(key=lambda n: n.layer)
                yield current_tick, chord
                current_tick, chord = note.tick, [note]
        yield current_tick, chord


class Parser(object):
    def __init__(self, buff):
        self.buffer = buff

    def read_file(self):
        values = self.parse_header()
        header = Header(**values)
        version = values['version']
        return File(header, list(self.parse_notes(version)),
                    list(self.parse_layers(header.song_layers, version)),
                    list(self.parse_instruments(version)))

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
        song_length = self.read_numeric(SHORT)
        if song_length == 0:
            # A song length of 0 indicates the Open Note Block Studio format
            version = self.read_numeric(BYTE)
        else:
            version = 0

        return {
            'version':             version,
            'default_instruments': self.read_numeric(BYTE)  if version > 0 else 10,
            'song_length':         self.read_numeric(SHORT) if version > 0 else song_length,
            'song_layers':         self.read_numeric(SHORT),
            'song_name':           self.read_string(),
            'song_author':         self.read_string(),
            'original_author':     self.read_string(),
            'description':         self.read_string(),

            'tempo':               self.read_numeric(SHORT) / 100.0,
            'auto_save':           self.read_numeric(BYTE) == 1,
            'auto_save_duration':  self.read_numeric(BYTE),
            'time_signature':      self.read_numeric(BYTE),

            'minutes_spent':       self.read_numeric(INT),
            'left_clicks':         self.read_numeric(INT),
            'right_clicks':        self.read_numeric(INT),
            'blocks_added':        self.read_numeric(INT),
            'blocks_removed':      self.read_numeric(INT),
            'song_origin':         self.read_string(),
            'loop':                self.read_numeric(BYTE) == 1 if version >= 4 else False,
            'max_loop_count':      self.read_numeric(BYTE)      if version >= 4 else 0,
            'loop_start':          self.read_numeric(SHORT)     if version >= 4 else 0
        }

    def parse_notes(self, version):
        for current_tick in self.jump():
            for current_layer in self.jump():
                instrument = self.read_numeric(BYTE)
                key        = self.read_numeric(BYTE)
                velocity   = self.read_numeric(BYTE)       if version >= 4 else 100
                panning    = self.read_numeric(BYTE) - 100 if version >= 4 else 0
                pitch      = self.read_numeric(SSHORT)     if version >= 4 else 0
                yield Note(current_tick, current_layer, instrument,
                           key, velocity, panning, pitch)

    def parse_layers(self, layers_count, version):
        for i in range(layers_count):
            name    = self.read_string()
            lock    = self.read_numeric(BYTE) == 0  if version >= 4 else False
            volume  = self.read_numeric(BYTE)
            panning = self.read_numeric(BYTE) - 100 if version >= 2 else 0
            yield Layer(i, name, lock, volume, panning)

    def parse_instruments(self, version):
        for i in range(self.read_numeric(BYTE)):
            name       = self.read_string()
            sound_file = self.read_string()
            pitch      = self.read_numeric(BYTE)
            press_key  = self.read_numeric(BYTE) == 1
            yield Instrument(i, name, sound_file, pitch, press_key)


class Writer(object):
    def __init__(self, buff):
        self.buffer = buff

    def encode_file(self, nbs_file, version):
        self.write_header(nbs_file, version)
        self.write_notes(nbs_file, version)
        self.write_layers(nbs_file, version)
        self.write_instruments(nbs_file, version)

    def encode_numeric(self, fmt, value):
        self.buffer.write(fmt.pack(value))

    def encode_string(self, value):
        self.encode_numeric(INT, len(value))
        self.buffer.write(value.encode())

    def write_header(self, nbs_file, version):
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

    def write_notes(self, nbs_file, version):
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

    def write_layers(self, nbs_file, version):
        for layer in nbs_file.layers:
            self.encode_string(layer.name)
            if version >= 4:
                self.encode_numeric(BYTE, int(layer.lock))
            self.encode_numeric(BYTE, layer.volume)
            if version >= 2:
                self.encode_numeric(BYTE, layer.panning + 100)

    def write_instruments(self, nbs_file, version):
        self.encode_numeric(BYTE, len(nbs_file.instruments))
        for instrument in nbs_file.instruments:
            self.encode_string(instrument.name)
            self.encode_string(instrument.file)
            self.encode_numeric(BYTE, instrument.pitch)
            self.encode_numeric(BYTE, int(instrument.press_key))
