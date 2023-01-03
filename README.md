`ObsidianToAnki` is a console application, which turns Obsidian app notes names into Anki notes, so it becomes possible to
use spaced repetition method to learn Obsidian notes.

Each run of `ObsidianToAnki` application fully synchronizes Obsidian notes folder with Anki collection.

The synchronization includes:
- editing Anki note name if related Obsidian note was renamed
- deleting Anki note if related Obsidian note was deleted
- adding new Anki notes for new Obsidian notes
- listing names of edited Obsidian notes, whose related Anki notes are in progress, so that user can decide whether 
  learning progress for them should be dropped.

# Usage
## Configuration
In `configs.py`:
- specify the path to Obsidian vault folder in `PATH_TO_OBSIDIAN_VAULT` constant.
- specify a name for default deck in `DEFAULT_DECK_NAME` constant or leave the default value ("Obsidian").
- specify other deck names in `All_DECK_NAMES` constant. Use comma as a separator. If there is no need for extra decks 
  creation, then do not modify this constant.
  
## Launching
Run the program with `python main.py` and wait until the result of synchronization outputs to the console.