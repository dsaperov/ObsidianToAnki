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
            deck_name = args[0]
            self.info(f'Создана колода {deck_name}')
        elif command == 'addNotes':
            self._log_add_notes_command_result(*args)
        elif command == 'deleteNotes':
            self._log_delete_notes_command_result(*args)
        else:
            self._log_update_notes_command_result(*args)

    def _log_add_notes_command_result(self, command_result, expected_added_notes_count, initial_adding, anki):
        command_result_processed = ['added' if note_id else 'fail' for note_id in command_result]
        added_notes_count = command_result_processed.count('added')
        fails_count = command_result_processed.count('fail')
        log_text = f'Добавлено карт в колоду: {added_notes_count} из {expected_added_notes_count}. Ошибок: ' \
                   f'{fails_count}.'

        if not initial_adding and added_notes_count:
            log_text += f'\nДобавленные карты:' + '\n'
            added_notes_ids = [note_id for note_id in command_result if note_id]
            added_notes_content = anki.get_content(added_notes_ids, 'notes')
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

    def log_obs_edited_notes_in_progress_found(self, edited_notes_cards_texts, obs_notes_new_names_for_old_names):
        self._modify_cards_texts(edited_notes_cards_texts, obs_notes_new_names_for_old_names)
        log_text = f'Поскольку некоторые заметки в Obsidian были изменены, для соответствующих им изученных карт ' \
                   f'(всего {len(edited_notes_cards_texts)}), возможно, следует сбросить прогресс.' + '\n'
        for note in edited_notes_cards_texts:
            log_text += f'- {note}' + '\n'
        self.info(log_text)

    @staticmethod
    def _modify_cards_texts(cards_texts, obs_notes_new_names_for_old_names):
        """Receives list with Anki cards texts. Checks whether any related to them Obsidian notes were renamed and if
        so, adds new names to old names in this list.
        """
        obs_renamed_notes_names = obs_notes_new_names_for_old_names.keys()
        for i in range(len(cards_texts)):
            card_text = cards_texts[i]
            if card_text in obs_renamed_notes_names:
                card_new_text = obs_notes_new_names_for_old_names[card_text]
                cards_texts[i] += f' (--> {card_new_text})'


logger = Logger('basic_logger')
logger.set_configs()
