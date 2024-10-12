import os
import re
import json
import zipfile
from pathlib import Path

# Словарь для хранения предустановленных переводов
translation_dict = {}

# Функция для загрузки словаря из файла JSON
def load_translation_dict(file_name):
    if os.path.exists(file_name):
        # Если файл существует, загружаем словарь
        with open(file_name, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    else:
        # Если файла нет, возвращаем пустой словарь
        return {
            "н": "n",  # No skill
            "о": "b",  # Basic skill
            "р": "a",  # Advanced skill
            "и": "e",  # Expert skill
            "ед.Жз.": "HP",  # HP
            "ед.Зд.": "HP",  # HP
        }


def translate_word(word, context):
    # Ищем слово в словаре, игнорируя регистр
    lowercase_word = word.lower()
    if lowercase_word in translation_dict:
        # Проверяем, была ли первая буква заглавной
        if word[0].isupper():
            return translation_dict[lowercase_word].capitalize()
        else:
            return translation_dict[lowercase_word]
    else:
        # Если слово не переведено, запрашиваем перевод у пользователя
        print(f"Новое слово найдено: {word}")
        print(f"Контекст перевода: {context}")
        translation = input("Введите перевод для этого слова: ")
        translation_dict[lowercase_word] = translation  # Добавляем перевод в словарь

        # Сохраняем регистр для заглавной буквы
        if word[0].isupper():
            return translation.capitalize()
        else:
            return translation


def translate_table(text, spell_name):
    # Функция для перевода строк таблицы
    translated_lines = []
    for line in text.split("\n"):
        result_line = ""
        tokens = re.split(r"([^а-яё\.-]+)", line, flags=re.IGNORECASE)
        for token in tokens:
            if not re.search("[а-я]", token, flags=re.IGNORECASE):
                result_line += token
                continue
            result_line += translate_word(token, line)
        translated_lines.append(result_line)
    return "\n".join(translated_lines)


def process_files(russian_folder, english_folder, mod_folder):
    file_desc_name = "Long_Description.txt"
    for root, dirs, files in os.walk(russian_folder):
        if file_desc_name in files:
            russian_file_path = os.path.join(root, file_desc_name)
            relative_path = os.path.relpath(root, russian_folder)

            # Чистим путь от "_!" в конце папок
            relative_path_cleaned = os.path.join(
                *[part.removesuffix("_!") for part in relative_path.split(os.sep)]
            )
            english_file_path = os.path.join(english_folder, relative_path_cleaned, file_desc_name)
            spell_name = root.rstrip(os.sep).split(os.sep)[-1]
            print(f"Started spell {spell_name}")

            with open(russian_file_path, "r", encoding="utf-16le") as russian_file:
                russian_text = russian_file.read()

            with open(english_file_path, "r", encoding="utf-16le") as english_file:
                english_text = english_file.read()

            if russian_text is None or english_text is None:
                print(f"spell {spell_name} error")
                continue

            # Копируем описание заклинания из английского
            description_part = english_text.split("\n\n", 1)[0]
            updated_text = description_part

            # Переводим таблицу силы
            split_content = russian_text.split("\n\n", 1)
            if len(split_content) > 1:
                table_part = split_content[1]
                translated_table = translate_table(table_part, spell_name)
                updated_text += "\n\n" + translated_table

            # Обновляем новый мод
            mod_path = os.path.join(mod_folder, relative_path)
            Path(mod_path).mkdir(parents=True, exist_ok=True)
            mod_file_path = os.path.join(mod_path, file_desc_name)
            with open(mod_file_path, "w", encoding="utf-16le") as mod_file:
                mod_file.write(updated_text)

            print(f"Spell {spell_name} done")


def get_all_russian():
    all_russian_words = {}

    for dirpath, dirnames, filenames in os.walk("russian"):
        if "Long_Description.txt" in filenames:
            spell_name = dirpath.rstrip("/").split("/")[-1]
            with open(
                os.path.join(dirpath, "Long_Description.txt"), "r", encoding="utf-16le"
            ) as file:
                # Разделяем по пустой строке (\n\n)
                split_content = file.read().split("\n\n", 1)
                if len(split_content) > 1:
                    second_part = split_content[
                        1
                    ]  # Вторая часть текста после первой пустой строки

                    # Ищем русские слова
                    words = re.findall(r"[а-яА-ЯёЁ\.]+", second_part)

                    for word in words:
                        if word not in all_russian_words:
                            all_russian_words[word] = spell_name
    print(all_russian_words)


# Функция для архивации папки в ZIP-архив
def create_zip(folder_path):
    with zipfile.ZipFile("spell_description_en.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Проходим по всем файлам в папке и добавляем их в архив
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Добавляем файл в архив, сохраняя структуру директорий
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
    os.rename("spell_description_en.zip", "spell_description_en.h5u")


if __name__ == "__main__":
    translation_dict_file = "translation_dict.json"
    translation_dict = load_translation_dict(translation_dict_file)
    russian_folder = "russian"
    english_folder = "english"
    mod_folder = "mod"
    process_files(russian_folder, english_folder, mod_folder)
    with open(translation_dict_file, "w", encoding="utf-8") as json_file:
        json.dump(translation_dict, json_file, ensure_ascii=False, indent=4)
    create_zip(mod_folder)
