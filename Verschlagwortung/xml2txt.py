# -*- coding: utf-8 -*-
import os
from bs4 import BeautifulSoup
import re

"""
1. Extracts text from TEI XML files (removing `<note>` elements and handling `<s>` and `<p>` content).
2. Writes the cleaned text to `.txt` files.
3. Deletes `.txt` files that are empty or have fewer than 3 lines.
4. Logs the deleted filenames to a file called `empty_files.txt`.
"""

# Paths
bullinger_path = '../../bullinger-korpus-tei/data/letters'
output_path = 'txts'
output_file = 'empty_files.txt'

# Ensure the output directory exists
if not os.path.exists(output_path):
    os.makedirs(output_path)

def extract_texts_from_xml(xml_file):
    text = ''
    with open(xml_file, 'r', encoding='utf-8') as tei:
        soup = BeautifulSoup(tei, features="xml")

        # Remove all <note> elements
        for note in soup.find_all('note'):
            note.decompose()

        # Extract from <s> elements
        for s in soup.find_all('s'):
            text += s.get_text() + '\n'

        # If no <s> elements, extract from <p> elements
        if not text:
            for p in soup.find_all('p'):
                par = " ".join(p.get_text().split())
                text += re.sub(r'(?<=[a-zA-Z]{4})\.\s', '.\n', par) + '\n'

    return text

def process_letters():
    for letter in os.listdir(bullinger_path):
        if letter.endswith('.xml'):
            xml_file = os.path.join(bullinger_path, letter)
            text = extract_texts_from_xml(xml_file)

            txt_file = os.path.join(output_path, letter.replace('.xml', '.txt'))
            with open(txt_file, 'w', encoding='utf-8') as txt:
                txt.write(text)

def clean_empty_or_short_files():
    empty_files = []

    for filename in os.listdir(output_path):
        file_path = os.path.join(output_path, filename)

        if filename.endswith(".txt") and os.path.isfile(file_path):
            is_empty = os.stat(file_path).st_size == 0
            has_few_lines = False

            with open(file_path, "r", encoding="utf-8") as infile:
                if len(infile.readlines()) < 3:
                    has_few_lines = True

            if is_empty or has_few_lines:
                empty_files.append(filename)
                os.remove(file_path)

    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write("\n".join(empty_files))

    print(f"Deleted {len(empty_files)} files. Saved list to {output_file}.")

def main():
    process_letters()
    clean_empty_or_short_files()

if __name__ == '__main__':
    main()
