import logging

from anki import Anki


class Logger(logging.Logger):

    def __init__(self, name):
        super().__init__(name)

    def set_configs(self):
        self.setLevel(logging.INFO)
        fh = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.addHandler(fh)

    def log_command_result(self, command, *args):
        """Receives command name and calls related logging method."""
        if command == 'createDeck':
            self.info(f'Создана колода {Anki.DEFAULT_DECK_NAME}')
        elif command == 'addNotes':
            self._log_add_notes_command_result(*args)
        elif command == 'deleteNotes':
            self._log_delete_notes_command_result(*args)
        elif command == 'updateNoteFields':
            self._log_update_notes_command_result(*args)
        else:
            self._log_drop_cards_progress_command_result(*args)

    def _log_add_notes_command_result(self, command_result, expected_added_notes_count, initial_adding, anki):
        command_result_processed = ['added' if note_id else 'fail' for note_id in command_result]
        added_notes_count = command_result_processed.count('added')
        fails_count = command_result_processed.count('fail')
        log_text = f'Добавлено карт в колоду: {added_notes_count} из {expected_added_notes_count}. Ошибок: ' \
                   f'{fails_count}.'

        if not initial_adding and added_notes_count:
            log_text += f'\nДобавленные карты:' + '\n'
            added_notes_ids = [note_id for note_id in command_result if note_id]
            added_notes_content = anki.get_notes_content(added_notes_ids)
            for note_content in added_notes_content:
                note_text = note_content['fields']['Лицевая сторона']['value']
                log_text += f'- {note_text}' + '\n'
        self.info(log_text)

    def _log_delete_notes_command_result(self, deleted_notes):
        log_text = f'Из колоды удалены карты (всего {len(deleted_notes)}):' + '\n'
        for note in deleted_notes:
            log_text += f'- {note}' + '\n'
        self.info(log_text)

    def _log_update_notes_command_result(self, notes_renamed):
        log_text = f'Переименованы следующие карты (всего {len(notes_renamed)}):' + '\n'
        for note_old_text, note_new_text in notes_renamed.items():
            log_text += f'- "{note_old_text}" --> "{note_new_text}"' + '\n'
        self.info(log_text)

    def _log_drop_cards_progress_command_result(self, edited_notes, notes_new_names_for_old_names):
        anki_texts_ = edited_notes['renamed']
        if edited_renamed_notes:

        # edited_notes_count = sum(len(notes) for notes in edited_notes.values())
        log_text = f'Поскольку некоторые заметки в Obsidian были изменены (всего {edited_notes_count}), для ' \
                   f'соответствующих им карт был сброшен прогресс:' + '\n'

        for note in edited_notes:
            log_text += f'- {note}' + '\n'
        self.info(log_text)


logger = Logger('basic_logger')
logger.set_configs()
