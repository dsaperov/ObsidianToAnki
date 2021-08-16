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

    def log_command_result(self, result, command, *args):
        if command == 'createDeck':
            self._log_create_deck_command_result(result)
        elif command == 'addNotes':
            self._log_add_notes_command_result(result, *args)
        elif command == 'deleteNotes':
            self._log_delete_notes_command_result(result, *args)

    def _log_create_deck_command_result(self, result):
        if not result['error']:
            log_text = f'Создана колода {Anki.DEFAULT_DECK_NAME}'
        else:
            log_text = 'При создании колоды произошла ошибка. Возможно, колода уже существует.'
        self.info(log_text)

    def _log_add_notes_command_result(self, command_results, expected_added_notes_count):
        command_results = ['added' if note_id else 'fail' for note_id in command_results]
        added_notes_count = command_results.count('added')
        fails_count = command_results.count('fail')
        log_text = f'Добавлено карт в колоду: {added_notes_count} из {expected_added_notes_count}. Ошибок: {fails_count}'
        self.info(log_text)

    def _log_delete_notes_command_result(self, command_results, expected_deleted_notes_ids, note_text_for_note_id):
        deletion_failed_notes_ids = [note_id for note_id in command_results if note_id]
        deleted_notes_ids = set(expected_deleted_notes_ids) - set(deletion_failed_notes_ids)
        deleted_notes = (note_text_for_note_id[note_id] for note_id in deleted_notes_ids)
        log_text = f'Удалено карт из колоды: {len(deleted_notes_ids)} из {len(expected_deleted_notes_ids)}. Ошибок: ' \
                   f'{len(deletion_failed_notes_ids)}'
        if deleted_notes:
            log_text += 'Удаленные карты:'
            for note in deleted_notes:
                log_text += '\n' + f'- {note}'
        self.info(log_text)


logger = Logger('basic_logger')
logger.set_configs()
