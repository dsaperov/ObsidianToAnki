import os
from datetime import datetime

from anki import CommandExecutor, Anki
from configs import SYNC_FILE_NAME
from obsidian import Obsidian
from logger import logger


class File:
    def __init__(self, name):
        self.name = name
        self.folder = os.path.dirname(os.path.realpath(__file__))

    def check_existence(self):
        filenames = os.walk(self.folder).__next__()[2]
        res = any(filename == self.name for filename in filenames)
        return res

    def update(self, content):
        file = open(self.name, mode='w', encoding='cp1251')
        file.write(content)
        file.close()

    def get_content(self):
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
        last_sync_date = sync_file.get_content()
        anki.parse_notes_data()
        obs.get_notes_changes(anki, last_sync_date)
        if obs.deleted_notes:
            notes_ids = [anki.notes_ids_for_notes_texts[note] for note in obs.deleted_notes]
            anki.delete_notes(notes_ids, obs.deleted_notes)
        if obs.added_notes:
            notes_ids = [anki.notes_ids_for_notes_texts[note] for note in obs.added_notes]
            anki.add_notes(notes_ids)
        if obs.renamed_notes_new_names:
            notes_ids = [anki.notes_ids_for_notes_texts[note] for note in obs.renamed_notes_old_names]
            anki.rename_notes(notes_ids)
            anki.drop_notes_progress(notes_ids)
        if obs.edited_notes:
            notes_ids = None
            anki.drop_notes_progress(notes_ids)

    else:
        # Если синхронизаций ранее не проводилось --> создать доску и выгрузить туда карточки с названиями заметок
        create_deck_result = anki.create_deck()
        notes_for_adding = anki.gen_notes_to_add(obs.notes_files_ids_for_notes_names)
        anki_added_notes = anki.add_notes(notes_for_adding)
        if any(anki_added_notes) is True:
            sync_file.update(new_sync_date)
            logger.info(f'Синхронизация завершена. Информация о дате и времени занесена в файл {sync_file.name}')
