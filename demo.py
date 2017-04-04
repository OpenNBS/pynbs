
from __future__ import print_function

import pynbs


my_file = pynbs.read('demo_song.nbs')

print(my_file.header.song_length)
print(my_file.header.description)

print(my_file.notes)
print(my_file.layers)
print(my_file.instruments)

for tick, chord in my_file.song():
    print(tick, [note.key for note in chord])
