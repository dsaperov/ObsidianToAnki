from collections import defaultdict
from copy import deepcopy
import json
import urllib.request


class Anki:
    """Anki notes collection."""
    DEFAULT_DECK_NAME = 'F. Obs_default'
    All_DECK_NAMES = [DEFAULT_DECK_NAME, 'A. Obs_new_review', 'B. Obs_new_retrieval', 'C. Obs_new_evaluation',
                      'D. Obs_rep_retrieval', 'E. Obs_rep_evaluation', 'G. Obs_next_lvl',
                      'H. Obsidian_not_for_learning']
    NOTE_TEMPLATE = {
        'deckName': DEFAULT_DECK_NAME,
        'modelName': 'Базовый',
        'fields': {
            'Лицевая сторона': '',
            'Оборотная сторона': 'Done!'
        },
        'tags': []
    }
    COMMANDS_FOR_OBJECTS_TYPES = {
        'notes': {
            'get_ids': 'findNotes',
            'get_content': 'notesInfo'
        },
        'cards': {
            'get_ids': 'findCards',
            'get_content': 'cardsInfo'
        }
    }

    def __init__(self, command_executor, logger):
        self.command_executor = command_executor
        self.logger = logger

        self.ids_for_texts = defaultdict(dict)
        self.note_texts_for_file_ids = {}
        self.cards_in_progress_texts = set()

    def create_decks(self):
        """Creates Anki decks."""
        for deck_name in self.All_DECK_NAMES:
            params = {'deck': deck_name}
            command = 'createDeck'
            self.command_executor.run(command, params)
            self.logger.log_command_result(command, deck_name)

    def gen_notes_to_add(self, files_ids_for_notes):
        """Generates list with notes in format, which is acceptable for "Anki connect" to work with."""
        notes_to_add = []
        for note, file_id in files_ids_for_notes.items():
            note_content = deepcopy(self.NOTE_TEMPLATE)
            note_content['fields']['Лицевая сторона'] = note
            note_content['tags'] = [file_id]
            notes_to_add.append(note_content)
        return notes_to_add

    def add_notes(self, notes, initial_adding=False):
        """Adds received notes to Anki collection."""
        params = {'notes': notes}
        command = 'addNotes'
        result = self.command_executor.run(command, params)['result']
        self.logger.log_command_result(command, result, len(notes), initial_adding, self)
        return result

    def parse_notes_data(self):
        """Parses Anki collection in order to retrieve existing notes data."""
        parsing_objects_type = 'notes'
        notes_ids = self._get_ids(parsing_objects_type)
        notes_content = self.get_content(notes_ids, parsing_objects_type)
        for note_content in notes_content:
            note_text = note_content['fields']['Лицевая сторона']['value']

            note_id = note_content['noteId']
            self.ids_for_texts[note_text]['note_id'] = note_id

            note_file_id = note_content['tags'][0]
            self.note_texts_for_file_ids[note_file_id] = note_text

    def parse_cards_data(self):
        parsing_objects_type = 'cards'
        cards_ids = self._get_ids(parsing_objects_type)
        cards_content = self.get_content(cards_ids, parsing_objects_type)
        for card_content in cards_content:
            card_text = card_content['fields']['Лицевая сторона']['value']
            card_id = card_content['cardId']
            self.ids_for_texts[card_text]['card_id'] = card_id
            self.cards_in_progress_texts.add(card_text) if card_content['interval'] else None

    def _get_ids(self, objects_type):
        """
        Returns list with ids for all existing objects of specified type in the Anki collection.
        :param str objects_type: type of objects which ids should be returned. It can be either 'notes' or 'cards'.
        """
        all_ids = []
        command = self.COMMANDS_FOR_OBJECTS_TYPES[objects_type]['get_ids']
        for deck_name in self.All_DECK_NAMES:
            params = {'query': f'"deck:{deck_name}"'}
            ids_by_deck = self.command_executor.run(command, params)['result']
            all_ids.extend(ids_by_deck)
        return all_ids

    def get_content(self, ids, objects_type):
        """
        Returns list with content for received objects ids.
        :param str objects_type: type of objects which ids were passed. It can be either 'notes' or 'cards'.
        """
        params = {objects_type: ids}
        command = self.COMMANDS_FOR_OBJECTS_TYPES[objects_type]['get_content']
        content = self.command_executor.run(command, params)['result']
        return content

    def delete_notes(self, notes_ids, notes_texts):
        """Returns notes from Anki collection according to received notes ids."""
        params = {'notes': notes_ids}
        command = 'deleteNotes'
        self.command_executor.run(command, params)
        self.logger.log_command_result(command, notes_texts)

    def update_notes(self, notes_ids, notes_old_texts, notes_new_texts):
        """
        Replace Anki note front side content with related Obsidian note new name for each Anki note, which id is in
        received notes_ids.
        """
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

    def relearn_cards(self, cards_ids, *obs_notes_data):
        """Switches status to "Relearn" for each card, which id is in received cards_ids."""
        params = {'cards': cards_ids}
        command = "relearnCards"
        self.command_executor.run(command, params)
        self.logger.log_command_result(command, *obs_notes_data)


class CommandExecutor:
    """CommandExecutor is responsible for direct interaction with Anki local server."""

    def run(self, command, params):
        """Runs the command executor."""
        json_bytes = self._get_json(command, params)
        response_result = self._send_request(json_bytes)
        return response_result

    @staticmethod
    def _get_json(command, params):
        """Generates JSON using received command and parameters."""
        data = {'action': command, 'params': params, 'version': 6}
        data_json = json.dumps(data)
        data_json_bytes = data_json.encode('utf-8')
        return data_json_bytes

    @staticmethod
    def _send_request(json_bytes):
        """Sends request to Anki local server and returns the response."""
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
