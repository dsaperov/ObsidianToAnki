`ObsidianToAnki` is a console application, which turns Obsidian app notes names into Anki notes, so it becomes possible to
use spaced repetition method to learn Obsidian notes.

Each run of `ObsidianToAnki` application fully synchronizes Obsidian notes folder with Anki collection.

The synchronization includes:
- editing Anki note name if related Obsidian note was renamed
- deleting Anki note if related Obsidian note was deleted
- dropping learning progress for Anki note if related Obsidian note was edited
- adding new Anki notes for new Obsidian notes