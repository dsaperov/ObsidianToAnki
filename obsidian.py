import os
import time
from datetime import datetime

from configs import PATH_TO_OBSIDIAN


class Obsidian:

    def __init__(self, logger):
        self.logger = logger

        self.notes_files_ids_for_notes_names = {}
        self.notes_names_for_mod_dates = {}
        self.notes_files_ids = set()
        self.notes_names = set()

        self.deleted_notes = set()
        self.added_notes = set()
        self.renamed_notes_new_names = set()
        self.renamed_notes_old_names = set()
        self.edited_notes = set()

    def parse_notes_stat_data(self):
        note_files = os.walk(PATH_TO_OBSIDIAN).__next__()[2]
        for note_file in note_files:
            path_to_file = os.path.join(PATH_TO_OBSIDIAN, note_file)

            note_file_id = str(os.stat(path_to_file, follow_symlinks=False).st_ino)
            self.notes_files_ids.add(note_file_id)

            note_name = note_file[:-3]
            self.notes_names.add(note_name)

            self.notes_files_ids_for_notes_names[note_name] = note_file_id

            note_modification_date = datetime.fromtimestamp(os.path.getmtime(path_to_file))
            self.notes_names_for_mod_dates[note_modification_date] = note_name

    def get_notes_changes(self, anki, last_sync_date):
        deleted_notes_files_ids = anki.notes_files_ids - self.notes_files_ids
        self.deleted_notes = [anki.notes_texts_for_notes_files_ids[file_id] for file_id in deleted_notes_files_ids]

        last_sync_date = datetime.strptime(last_sync_date, '%Y-%m-%d %H:%M:%S:%f')
        for mod_date, note_name in self.notes_names_for_mod_dates.items():
            if mod_date >= last_sync_date:
                if note_name in anki.notes_texts:
                    self.edited_notes.add(note_name)
                else:
                    note_file_id = self.notes_files_ids_for_notes_names[note_name]
                    if note_file_id in anki.notes_files_ids:
                        self.renamed_notes_new_names.add(note_name)
                        note_old_name = anki.notes_texts_for_notes_files_ids[note_file_id]
                        self.renamed_notes_old_names.add(note_old_name)
                    else:
                        self.added_notes.add(note_name)


