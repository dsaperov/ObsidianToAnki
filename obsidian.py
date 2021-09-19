from collections import defaultdict
from datetime import datetime
import os
from configs import PATH_TO_OBSIDIAN_VAULT


class Obsidian:
    """Obsidian notes data."""

    def __init__(self, logger):
        self.logger = logger

        # self.mod_dates_for_notes_names = {}
        # self.notes_files_ids_for_notes_names = {}
        # self.notes_files_ids = set()

        self.notes_data = {}

        self.deleted_notes_names = set()
        self.added_notes_names = set()
        self.notes_new_names_for_old_names = {}
        self.edited_notes_names = defaultdict(set)
        # self.renamed_notes_new_names = []
        # self.renamed_notes_old_names = []
        # self.edited_non_renamed_notes_names = set()
        # self.edited_renamed_notes_old_names = set()

    def parse_notes_stat_data(self):
        """Parses Obsidian vault folder to glean up-to-date notes files data."""
        note_files = os.walk(PATH_TO_OBSIDIAN_VAULT).__next__()[2]
        for note_file in note_files:
            path_to_file = os.path.join(PATH_TO_OBSIDIAN_VAULT, note_file)

            note_file_id = str(os.stat(path_to_file, follow_symlinks=False).st_ino)
            # self.notes_files_ids.add(note_file_id)

            note_name = note_file[:-3]
            # self.notes_names.add(note_name)

            # self.notes_files_ids_for_notes_names[note_name] = note_file_id
            self.notes_data[note_name] = {}
            self.notes_data[note_name]['file_id'] = note_file_id

            note_modification_date = datetime.fromtimestamp(os.path.getmtime(path_to_file))
            self.notes_data[note_name]['modification_date'] = note_modification_date

    def get_notes_changes(self, anki, last_sync_date):
        """Defines Obsidian notes changes happened after the last synchronization."""
        obs_files_ids = set(note_data['file_id'] for note_data in self.notes_data.values())
        anki_notes_files_ids = set(anki.notes_files_data.keys())
        deleted_notes_files_ids = anki_notes_files_ids - obs_files_ids
        self.deleted_notes_names = [anki.notes_files_data[file_id]['note_text'] for file_id in deleted_notes_files_ids]

        last_sync_date = datetime.strptime(last_sync_date, '%Y-%m-%d %H:%M:%S:%f')
        for note_name, note_data in self.notes_data.items():
            mod_date = note_data['modification_date']
            note_file_id = self.notes_data[note_name]['file_id']
            # note_file_id = self.notes_files_ids_for_notes_names[note_name]
            if note_file_id in anki_notes_files_ids:
                anki_notes_texts = anki.ids_for_anki_texts.keys()
                if note_name in anki_notes_texts:
                    if mod_date >= last_sync_date:
                        self.edited_notes_names['non_renamed'].add(note_name)
                        # self.edited_non_renamed_notes_names.add(note_name)
                else:
                    note_old_name = anki.notes_files_data[note_file_id]['note_text']
                    # note_old_name = anki.notes_texts_for_notes_files_ids[note_file_id]
                    self.notes_new_names_for_old_names[note_old_name] = note_name
                    # self.renamed_notes_old_names.append(note_old_name)
                    # self.renamed_notes_new_names.append(note_name)
                    if mod_date >= last_sync_date:
                        self.edited_notes_names['renamed_old'].add(note_old_name)
                        # self.edited_renamed_notes_old_names.add(note_old_name)
            else:
                self.added_notes_names.add(note_name)


