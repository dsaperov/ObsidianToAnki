from collections import defaultdict
from datetime import datetime
import os
from configs import PATH_TO_OBSIDIAN_VAULT


class Obsidian:
    """Obsidian notes data."""

    def __init__(self, logger):
        self.logger = logger

        self.notes_data = defaultdict(dict)
        self.deleted_notes_names = set()
        self.added_notes_names = set()
        self.notes_new_names_for_old_names = {}
        self.edited_notes_names = set()

    def parse_notes_stat_data(self):
        """Parses Obsidian vault folder to glean up-to-date notes files data."""
        note_files = os.walk(PATH_TO_OBSIDIAN_VAULT).__next__()[2]
        for note_file in note_files:
            path_to_file = os.path.join(PATH_TO_OBSIDIAN_VAULT, note_file)
            note_file_id = str(os.stat(path_to_file, follow_symlinks=False).st_ino)
            note_name = note_file[:-3]
            self.notes_data[note_name]['file_id'] = note_file_id

            note_modification_date = datetime.fromtimestamp(os.path.getmtime(path_to_file))
            self.notes_data[note_name]['modification_date'] = note_modification_date

        notes_data_sorted = sorted(self.notes_data.items(), key=lambda item: item[1]['modification_date'])
        self.notes_data = dict(notes_data_sorted)

    def get_notes_changes(self, anki, last_sync_date):
        """Defines Obsidian notes changes happened after the last synchronization."""
        obs_files_ids = set(note_data['file_id'] for note_data in self.notes_data.values())
        anki_notes_files_ids = set(anki.note_texts_for_file_ids.keys())
        anki_notes_texts = anki.ids_for_texts.keys()
        deleted_notes_files_ids = anki_notes_files_ids - obs_files_ids
        self.deleted_notes_names = [anki.note_texts_for_file_ids[file_id] for file_id in deleted_notes_files_ids]

        last_sync_date = datetime.strptime(last_sync_date, '%Y-%m-%d %H:%M:%S:%f')
        for note_name, note_data in self.notes_data.items():
            mod_date = note_data['modification_date']
            note_file_id = self.notes_data[note_name]['file_id']

            if note_file_id in anki_notes_files_ids:
                if note_name not in anki_notes_texts:
                    note_name, note_new_name = anki.note_texts_for_file_ids[note_file_id], note_name
                    self.notes_new_names_for_old_names[note_name] = note_new_name
                if mod_date >= last_sync_date:
                    self.edited_notes_names.add(note_name)
            else:
                self.added_notes_names.add(note_name)


