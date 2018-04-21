from __future__ import print_function

import pynbs


# read file

my_file = pynbs.read('demo_song.nbs')

print(my_file.header.song_length)
print(my_file.header.description)

print(my_file.notes)
print(my_file.layers)
print(my_file.instruments)

for tick, chord in my_file:
    print(tick, [note.key for note in chord])


# new file

new_file = pynbs.blank_file()


# edit file

new_file.notes = [
    pynbs.Note(tick=0, layer=0, instrument=0, key=45),
    pynbs.Note(tick=2, layer=0, instrument=0, key=45),
    pynbs.Note(tick=4, layer=0, instrument=0, key=45),
    pynbs.Note(tick=6, layer=0, instrument=0, key=45),
    pynbs.Note(tick=8, layer=0, instrument=0, key=45),
]

new_file.header.song_name = 'foo'
new_file.header.song_author = 'bar'
new_file.header.blocks_added = 9000

new_file.save('new_file.nbs')
