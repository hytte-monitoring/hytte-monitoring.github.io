# 1 · Playlist

The smallest complete example: three classes, implemented exactly as designed.

**Result: 100 % alignment** — all 16 elements identical.

Run it with **Ctrl+Shift+B** (Cmd+Shift+B on macOS) and choose `1-class-simple`, then open
[`reports/class-report.md`](reports/class-report.md).

## The design

| Class | Has |
|---|---|
| `Playlist` | a name; `add(Song)`, `size()`, `totalDurationSeconds()` |
| `Song` | a title and a duration; getters, including `getArtist()` |
| `Artist` | a name; `getName()` |

Two relations, and they are the two you most need to tell apart:

| In the design | In C++ | Meaning |
|---|---|---|
| `Playlist *-- "*" Song` — **composition**, filled diamond | `std::vector<Song> songs_;` | the playlist **owns** its songs; they go when it goes |
| `Song --> Artist` — **association**, open arrow | `const Artist* artist_;` | a song **refers to** its artist; the artist lives on without it |

Compare [`playlist.hpp`](impl/include/music/playlist.hpp) and
[`song.hpp`](impl/include/music/song.hpp) with the design to see both.

## Try this

Break the implementation on purpose, run the task again, and watch the report and the
colour-coded comparison change:

| Edit | Result |
|---|---|
| in `song.hpp`, make `durationSeconds_` a `double` | ✏️ changed attribute, amber — 93.8 % |
| delete `getTitle()` from `song.hpp` and `song.cpp` | ➖ missing method, red — 93.8 % |
| add `int getSongCount() const { return 0; }` to `artist.hpp` | ➕ extra method, green — 94.1 % |
| make `artist_` a reference, `const Artist& artist_;` (and adjust `song.cpp`) | still 100 % — a reference is also an association |

Then undo your changes (`git checkout examples/1-class-simple`) to get back to 100 %.

## Files

```
diagrams/input/class.drawio     the design                              ← input
impl/include/music/*.hpp        the implementation's headers (compared)  ← input
impl/src/*.cpp                  the implementation's sources (built, not compared)
diagrams/output/                generated: class-design.mmd, class-implemented.mmd,
                                           class-comparison.drawio
reports/class-report.md         generated: the report
```
