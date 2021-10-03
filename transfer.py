import os

from configs import PATH_TO_OBSIDIAN_VAULT
from anki import Anki, CommandExecutor
from obsidian import Obsidian


class AnkiTransfer(Anki):

    def __init__(self, command_executor):
        self.command_executor = command_executor

        self.note_ids_for_file_ids = {}
        self.note_texts_for_file_ids = {}

    def parse_notes_data(self):
        notes_ids = self._get_notes_ids()

        notes_content = self.get_notes_content(notes_ids)
        for note_content in notes_content:
            note_text = note_content['fields']['Лицевая сторона']['value']
            note_id = note_content['noteId']
            note_file_id = note_content['tags'][0]

            self.note_ids_for_file_ids[note_file_id] = note_id
            self.note_texts_for_file_ids[note_file_id] = note_text

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
        print('Актуальные file_id для Obsidian-заметок:')
        for note_name, file_id in self.file_ids_for_note_names.items():
            print(f'{note_name} - {file_id}')
        print()

    @staticmethod
    def enumerate_notes(notes_names):
        notes_names_enumerated = {str(number): note_name for number, note_name in enumerate(notes_names, 1)}
        return notes_names_enumerated


if __name__ == '__main__':
    executor = CommandExecutor()
    anki_transfer = AnkiTransfer(executor)
    obsidian_transfer = ObsidianTransfer()

    anki_transfer.parse_notes_data()
    obsidian_transfer.parse_notes_stat_data()
    obsidian_transfer.print_parsed_data()

    anki_notes_file_ids = set(anki_transfer.note_ids_for_file_ids.keys())
    obsidian_notes_file_ids = set(obsidian_transfer.file_ids_for_note_names.values())
    obsidian_notes_new_file_ids = set(obsidian_notes_file_ids - anki_notes_file_ids)
    file_ids_modified = (anki_notes_file_ids - obsidian_notes_file_ids)
    print(f'Необходимо заменить тегов: {len(file_ids_modified)}\n')

    replaced_tags = 0
    for file_id in file_ids_modified:
        anki_note_id = anki_transfer.note_ids_for_file_ids[file_id]
        anki_note_text = anki_transfer.note_texts_for_file_ids[file_id]
        if anki_note_text not in obsidian_transfer.file_ids_for_note_names:
            no_file_id_text = f'В колоде есть карточка {anki_note_text}. В хранилище Obsidian не удалось найти ' \
                              f'заметку с таким именем. Если она была переименована, выберите номер, ' \
                              f'соответствующий ее новому имени. Если она была удалена, то введите "deleted".'
            print(no_file_id_text)

            obsidian_notes_new_file_ids_names = {note_name for note_name, file_id in
                                                 obsidian_transfer.file_ids_for_note_names.items() if
                                                 file_id in obsidian_notes_new_file_ids}
            obsidian_notes_new_file_ids_names_enumerated = ObsidianTransfer.enumerate_notes(
                obsidian_notes_new_file_ids_names)
            for number, note_name in obsidian_notes_new_file_ids_names_enumerated.items():
                print(f'{number}. {note_name}')

            choice = input()

            acceptable_input = obsidian_notes_new_file_ids_names_enumerated.keys() | {'deleted'}
            while choice not in acceptable_input:
                choice = input('Введите номер или "delete"\n')
            if choice in obsidian_notes_new_file_ids_names_enumerated.keys():
                anki_note_text = obsidian_notes_new_file_ids_names_enumerated[choice]
            else:
                continue

        new_file_id = obsidian_transfer.file_ids_for_note_names[anki_note_text]
        res = anki_transfer.replace_tag(anki_note_id, file_id, new_file_id)
        if not res['error']:
            replaced_tags += 1
            print(f'Заменено тегов - {replaced_tags} из {len(file_ids_modified)}', end="\r")
