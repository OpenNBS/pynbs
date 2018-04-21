# pynbs

A simple python library to read and write [.nbs files](http://www.stuffbydavid.com/mcnbs/format)
from [Note Block Studio](http://www.stuffbydavid.com/mcnbs). Compatible with
python 2 and 3.

## Reading files

```python
import pynbs

my_file = pynbs.read('demo_song.nbs')
print(my_file.header.tempo)
print(my_file.notes)

for tick, chord in my_file.song():
    print(tick, [note.key for note in chord])
```

### read(filename)

Read and parse the file at the specified location.

### File.header

The header holds all the fields that are defined in the file header.

Attribute          | Type    | Details
:------------------|:--------|:------------------------------------------------
song_length        | `int`   | The length of the song, measured in ticks.
song_layers        | `int`   | The id of the last layer with at least one note block in it.
song_name          | `str`   | The name of the song.
song_author        | `str`   | The author of the song.
original_author    | `str`   | The original song author of the song.
description        | `str`   | The description of the song.
tempo              | `float` | The tempo of the song.
auto_save          | `bool`  | Whether auto-saving has been enabled.
auto_save_duration | `int`   | The amount of minutes between each auto-save.
time_signature     | `int`   | The time signature of the song.
minutes_spent      | `int`   | The amount of minutes spent on the project.
left_clicks        | `int`   | The amount of times the user have left clicked.
right_clicks       | `int`   | The amount of times the user have right clicked.
blocks_added       | `int`   | The amount of times the user have added a block.
blocks_removed     | `int`   | The amount of times the user have removed a block.
song_origin        | `str`   | The file name of the original midi or schematic.

For more information check out the [official specification](http://www.stuffbydavid.com/mcnbs/format).

### File.notes

This is a list of all the notes of the song in order. Each note has the
following attributes:

Attribute  | Type  | Details
:--------- |:------|:------------------------------------------------
tick       | `int` | The tick at which the note plays.
layer      | `int` | The id of the layer in which the note is placed.
instrument | `int` | The id of the instrument.
key        | `int` | The key of the note. (between 0 and 87)

### File.layers

A list of all the layers of the song in order. Each layer has the following
attributes:

Attribute | Type  | Details
:---------|:------|:------------------------
id        | `int` | The id of the layer.
name      | `str` | The name of the layer.
volume    | `int` | The volume of the layer.

### File.instruments

A list of all the custom instruments of the song in order. Each instrument has
the following attributes:

Attribute | Type   | Details
:---------|:-------|:----------------------------------------------------------
id        | `int`  | The id of the instrument.
name      | `str`  | The name of the instrument.
file      | `str`  | The name of the sound file of the instrument.
pitch     | `int`  | The pitch of the instrument. (between 0 and 87)
press_key | `bool` | Whether the piano should automatically press keys with the instrument when the marker passes them.

### File.song()

Returns a generator that yields consecutively all the chords of the song with
the associated tick:

```python
for tick, chord in my_file.song():
    ...
```

`chord` is a list of all the notes that play during the tick `tick`.

## Editing and saving files

```python
import pynbs

new_file = pynbs.blank_file()
new_file.header.song_name = 'Hello world'
new_file.notes = [pynbs.Note(tick=i, layer=0, instrument=0, key=i + 35)
                  for i in range(10)]

new_file.save('new_file.nbs')
```

### blank_file()

Create a new blank nbs file.

### File.save(filename)

Encode and write the file to the specified location.

---

License - [MIT](https://github.com/vberlier/pynbs/blob/master/LICENSE)
