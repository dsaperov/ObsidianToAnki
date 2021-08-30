"""
ObsidianToAnki is a console application, which turns Obsidian app notes names into Anki notes, so it becomes possible to
use spaced repetition method to learn Obsidian notes.

Each run of ObsidianToAnki application fully synchronizes Obsidian notes folder with Anki collection.

The synchronization includes:
- editing Anki note name if related Obsidian note was renamed
- deleting Anki note if related Obsidian note was deleted
- dropping learning progress for Anki note if related Obsidian note was edited
- adding new Anki notes for new Obsidian notes
"""

from datetime import datetime
import os

from anki import CommandExecutor, Anki

try:
    from configs import SYNC_FILE_NAME
except ImportError:
    exit('Do "cp config.py.default config.py" and set the PATH_TO_OBSIDIAN_VAULT')

from logger import logger
from obsidian import Obsidian


class File:
    def __init__(self, name):
        self.name = name
        self.folder = os.path.dirname(os.path.realpath(__file__))

    def check_existence(self):
        """Checks the file existence."""
        filenames = os.walk(self.folder).__next__()[2]
        res = any(filename == self.name for filename in filenames)
        return res

    def update(self, content):
        """Edits the file."""
        file = open(self.name, mode='w', encoding='cp1251')
        file.write(content)
        file.close()

    def get_content(self):
        """Retrieves and returns the file content."""
        file = open(self.name, mode='r', encoding='utf-8')
        content = file.read()
        file.close()
        return content


if __name__ == '__main__':
    sync_file = File(name=SYNC_FILE_NAME)
    anki_command_executor = CommandExecutor()
    anki = Anki(anki_command_executor, logger)
    obs = Obsidian(logger)
    sync_file_exists = sync_file.check_existence()
    new_sync_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')

    obs.parse_notes_stat_data()

    if sync_file_exists:
        # Sync file exists -> detect Obsidian notes updates made since the last synchronization
        last_sync_date = sync_file.get_content()
        anki.parse_notes_data()
        obs.get_notes_changes(anki, last_sync_date)

        if obs.deleted_notes:
            notes_ids = [anki.notes_ids_for_notes_texts[note] for note in obs.deleted_notes]
            anki.delete_notes(notes_ids, obs.deleted_notes)
        if obs.added_notes:
            added_notes_files_ids_for_notes_names = {note_name: obs.notes_files_ids_for_notes_names[note_name] for
                                                     note_name in obs.added_notes}
            notes_for_adding = anki.gen_notes_to_add(added_notes_files_ids_for_notes_names)
            anki.add_notes(notes_for_adding)
        if obs.renamed_notes_new_names:
            notes_ids = [anki.notes_ids_for_notes_texts[note] for note in obs.renamed_notes_old_names]
            anki.update_notes(notes_ids, obs.renamed_notes_old_names, obs.renamed_notes_new_names)

        edited_notes = list(obs.edited_non_renamed_notes | obs.edited_renamed_notes_old_names)
        if edited_notes:
            card_ids = [anki.notes_ids_for_notes_texts[note] for note in edited_notes]
            if obs.edited_renamed_notes_old_names:
                obs_notes_new_names_for_old_names = dict(zip(obs.renamed_notes_old_names, obs.renamed_notes_new_names))
                for i in range(len(edited_notes)):
                    note = edited_notes[i]
                    if note in obs.edited_renamed_notes_old_names:
                        new_name = obs_notes_new_names_for_old_names[note]
                        edited_notes[i] += f' (--> {new_name})'
            anki.drop_cards_progress(card_ids, edited_notes)

        if not any([obs.deleted_notes, obs.added_notes, obs.renamed_notes_new_names, edited_notes]):
            logger.info(f'С момента последней синхронизации не обнаружено никаких изменений.')

    else:
        # No sync file -> create Anki deck and generate an Anki note for each Obsidian note with Obsidian note name as a
        # front side content
        create_deck_result = anki.create_deck()
        notes_for_adding = anki.gen_notes_to_add(obs.notes_files_ids_for_notes_names)
        anki_added_notes = anki.add_notes(notes_for_adding, initial_adding=True)
        if not any(anki_added_notes) is True:
            logger.info(f'Синхронизация не была проведена. Возможно, в указанном каталоге отсутствуют заметки Obsidian.')
            exit()

    sync_file.update(new_sync_date)
    logger.info(f'Синхронизация завершена. Информация о дате и времени занесена в файл {sync_file.name}')
