from copy import deepcopy
import json
import urllib.request


class Anki:
    DEFAULT_DECK_NAME = 'Obsidian'
    NOTE_TEMPLATE = {
        'deckName': DEFAULT_DECK_NAME,
        'modelName': 'Базовый',
        'fields': {
            'Лицевая сторона': '',
            'Оборотная сторона': 'Done!'
        },
        'tags': []
    }

    def __init__(self, command_executor, logger):
        self.command_executor = command_executor
        self.logger = logger

        self.notes_texts = set()
        self.notes_ids = set()
        self.notes_ids_for_notes_texts = {}
        # self.cards_ids_for_notes_texts = {}
        self.notes_files_ids = set()
        self.notes_texts_for_notes_files_ids = {}
        self.new_names_for_renamed_notes = {}

    def create_deck(self):
        params = {'deck': self.DEFAULT_DECK_NAME}
        command = 'createDeck'
        self.command_executor.run(command, params)
        self.logger.log_command_result(command)

    def gen_notes_to_add(self, files_ids_for_notes):
        notes_to_add = []
        for note, file_id in files_ids_for_notes.items():
            note_content = deepcopy(self.NOTE_TEMPLATE)
            note_content['fields']['Лицевая сторона'] = note
            note_content['tags'] = [file_id]
            notes_to_add.append(note_content)
        return notes_to_add

    def add_notes(self, notes, initial_adding=False):
        params = {'notes': notes}
        command = 'addNotes'
        result = self.command_executor.run(command, params)['result']
        self.logger.log_command_result(command, result, len(notes), initial_adding, self)
        return result

    def parse_notes_data(self):
        notes_ids = self._get_notes_ids()
        notes_content = self.get_notes_content(notes_ids)
        for note_content in notes_content:
            note_text = note_content['fields']['Лицевая сторона']['value']
            self.notes_texts.add(note_text)

            note_id = note_content['noteId']
            self.notes_ids.add(note_id)
            self.notes_ids_for_notes_texts[note_text] = note_id

            note_file_id = note_content['tags'][0]
            self.notes_files_ids.add(note_file_id)
            self.notes_texts_for_notes_files_ids[note_file_id] = note_text

    def _get_notes_ids(self):
        params = {'query': f'deck:{self.DEFAULT_DECK_NAME}'}
        notes_ids = self.command_executor.run('findNotes', params)['result']
        return notes_ids

    def get_notes_content(self, notes_ids):
        params = {"notes": notes_ids}
        notes_content = self.command_executor.run('notesInfo', params)['result']
        return notes_content

    def delete_notes(self, notes_ids, notes_texts):
        params = {'notes': notes_ids}
        command = 'deleteNotes'
        self.command_executor.run(command, params)
        self.logger.log_command_result(command, notes_texts)

    def update_notes(self, notes_ids, notes_old_texts, notes_new_texts):
        notes_renamed = {}
        command = 'updateNoteFields'
        for note_id, note_old_text, note_new_text in zip(notes_ids, notes_old_texts, notes_new_texts):
            note_content = deepcopy(self.NOTE_TEMPLATE)
            note_content['id'] = note_id
            note_content['fields']['Лицевая сторона'] = note_new_text

            params = {'note': note_content}
            self.command_executor.run(command, params)
            notes_renamed[note_old_text] = note_new_text

        self.logger.log_command_result(command, notes_renamed)

    def drop_cards_progress(self, cards_ids, notes_texts):
        params = {'cards': cards_ids}
        command = 'forgetCards'
        self.command_executor.run(command, params)
        self.logger.log_command_result(command, notes_texts)


class CommandExecutor:

    def run(self, command, params):
        json_bytes = self._get_json(command, params)
        response_result = self._send_request(json_bytes)
        return response_result

    @staticmethod
    def _get_json(command, params):
        data = {'action': command, 'params': params, 'version': 6}
        data_json = json.dumps(data)
        data_json_bytes = data_json.encode('utf-8')
        return data_json_bytes

    @staticmethod
    def _send_request(json_bytes):
        request_object = urllib.request.Request('http://localhost:8765', json_bytes)
        response = urllib.request.urlopen(request_object)
        response_dict = json.load(response)
        if len(response_dict) != 2:
            raise Exception('response has an unexpected number of fields')
        if 'error' not in response_dict:
            raise Exception('response is missing required error field')
        if 'result' not in response_dict:
            raise Exception('response is missing required result field')
        if response_dict['error'] is not None:
            raise Exception(response_dict['error'])
        return response_dict
