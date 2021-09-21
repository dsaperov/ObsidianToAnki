import os

from configs import PATH_TO_OBSIDIAN_VAULT
from anki import Anki, CommandExecutor
from obsidian import Obsidian


class AnkiTransfer(Anki):

    def __init__(self, command_executor):
        self.command_executor = command_executor

        self.notes_count = 0
        self.note_texts_for_note_ids = {}
        self.file_ids_for_note_ids = {}

    def parse_notes_data(self):
        notes_ids = self._get_notes_ids()
        self.notes_count = len(notes_ids)
        print(f'В колоде найдено карт - ({self.notes_count})')

        notes_content = self.get_notes_content(notes_ids)
        for note_content in notes_content:
            note_text = note_content['fields']['Лицевая сторона']['value']
            note_id = note_content['noteId']
            note_file_id = note_content['tags'][0]

            self.note_texts_for_note_ids[note_id] = note_text
            self.file_ids_for_note_ids[note_id] = note_file_id

    def replace_tag(self, note_id, tag_to_replace, replace_with_tag):
        params = {
            "notes": [note_id, ],
            "tag_to_replace": tag_to_replace,
            "replace_with_tag": replace_with_tag
        }
        command = 'replaceTags'
        result = self.command_executor.run(command, params)
        return result


class ObsidianTransfer(Obsidian):

    def __init__(self):
        self.file_ids_for_note_names = {}

    def parse_notes_stat_data(self):
        note_files = os.walk(PATH_TO_OBSIDIAN_VAULT).__next__()[2]
        for note_file in note_files:
            path_to_file = os.path.join(PATH_TO_OBSIDIAN_VAULT, note_file)
            note_file_id = str(os.stat(path_to_file, follow_symlinks=False).st_ino)
            note_name = note_file[:-3]
            self.file_ids_for_note_names[note_name] = note_file_id

    def print_parsed_data(self):
        for note_name, file_id in self.file_ids_for_note_names.items():
            print(f'{note_name} - {file_id}')


if __name__ == '__main__':
    executor = CommandExecutor()
    anki_transfer = AnkiTransfer(executor)
    obsidian_transfer = ObsidianTransfer()

    anki_transfer.parse_notes_data()
    obsidian_transfer.parse_notes_stat_data()
    obsidian_transfer.print_parsed_data()

    replaced_tags = 0
    for note_id, note_text in anki_transfer.note_texts_for_note_ids.items():
        old_file_id = anki_transfer.file_ids_for_note_ids[note_id]
        new_file_id = obsidian_transfer.file_ids_for_note_names[note_text]
        res = anki_transfer.replace_tag(note_id, old_file_id, new_file_id)
        if not res['error']:
            replaced_tags += 1
            print(f'Заменено тегов - {replaced_tags} из {anki_transfer.notes_count}')

    print(f'Заменены теги в {replaced_tags} карточках')
