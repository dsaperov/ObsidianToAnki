from datetime import datetime
import os

from anki import CommandExecutor, Anki

try:
    from configs import SYNC_FILE_NAME
except ImportError:
    exit('Do "cp config.py.default config.py" and set the PATH_TO_OBSIDIAN_VAULT. Specify DEFAULT_DECK_NAME and '
         'All_DECK_NAMES if needed.')

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
        anki.parse_cards_data()
        obs.get_notes_changes(anki, last_sync_date)

        if obs.deleted_notes_names:
            notes_ids = [anki.ids_for_texts[note_name]['note_id'] for note_name in obs.deleted_notes_names]
            anki.delete_notes(notes_ids, obs.deleted_notes_names)

        if obs.added_notes_names:
            added_notes_files_ids_for_notes_names = {note_name: obs.notes_data[note_name]['file_id'] for note_name in
                                                     obs.added_notes_names}
            notes_for_adding = anki.gen_notes_to_add(added_notes_files_ids_for_notes_names)
            anki.add_notes(notes_for_adding)

        obs_renamed_notes_new_names = obs.notes_new_names_for_old_names.values()
        if obs_renamed_notes_new_names:
            obs_renamed_notes_old_names = obs.notes_new_names_for_old_names.keys()
            notes_ids = [anki.ids_for_texts[note_name]['note_id'] for note_name in obs_renamed_notes_old_names]
            anki.update_notes(notes_ids, obs_renamed_notes_old_names, obs_renamed_notes_new_names)

        obs_edited_notes_in_progress = obs.edited_notes_names & anki.cards_in_progress_texts
        if obs_edited_notes_in_progress:
            logger.log_obs_edited_notes_in_progress_found(sorted(list(obs_edited_notes_in_progress)),
                                                          obs.notes_new_names_for_old_names)

        if not any([obs.deleted_notes_names, obs.added_notes_names, obs_renamed_notes_new_names,
                    obs_edited_notes_in_progress]):
            logger.info(f'С момента последней синхронизации не обнаружено никаких изменений.')

    else:
        # No sync file -> create Anki deck and generate an Anki note for each Obsidian note with Obsidian note name as a
        # front side content
        create_deck_result = anki.create_decks()
        files_ids_for_notes = {note: note_data['file_id'] for note, note_data in obs.notes_data.items()}
        notes_for_adding = anki.gen_notes_to_add(files_ids_for_notes)
        anki_added_notes = anki.add_notes(notes_for_adding, initial_adding=True)
        if not any(anki_added_notes) is True:
            logger.info(f'Синхронизация не была проведена. Возможно, в указанном каталоге отсутствуют заметки Obsidian.'
                        )
            exit()

    sync_file.update(new_sync_date)
    logger.info(f'Синхронизация завершена. Информация о дате и времени занесена в файл {sync_file.name}')
