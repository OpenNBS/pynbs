from __future__ import print_function

import pynbs


# Read file

demo_song = pynbs.read('demo_song.nbs')

print(demo_song.header.song_length)
print(demo_song.header.description)

print(demo_song.notes)
print(demo_song.layers)
print(demo_song.instruments)

for tick, chord in demo_song:
    print(tick, [note.key for note in chord])


# Create new file

new_file = pynbs.new_file(
    song_name='foo',
    song_author='bar',
)


# Edit file

new_file.notes.extend([
    pynbs.Note(tick=0, layer=0, instrument=0, key=45),
    pynbs.Note(tick=2, layer=0, instrument=0, key=45),
    pynbs.Note(tick=4, layer=0, instrument=0, key=45),
    pynbs.Note(tick=6, layer=0, instrument=0, key=45),
    pynbs.Note(tick=8, layer=0, instrument=0, key=45),
])

new_file.header.blocks_added = 9000


# Save file

new_file.save('new_file.nbs')
