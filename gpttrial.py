
from docx import Document
import json
import os
import re

INPUT_PATH = "PromoCanon/Saving_Nora_CHARACTER BIBLE.docx"
OUTPUT_DIR = "context/characters"

os.makedirs(OUTPUT_DIR, exist_ok=True)

CHARACTERS = ["NORA SMITH", "JUSTIN HUNT", "HENRY SMITH"]

SECTION_MAP = {
    "1)": "character_snapshot",
    "2)": "voice_dna",
    "3)": "worldview_psychology",
    "4)": "interaction_rules",
    "5)": "canon_knowledge",
    "6)": "dialogue_examples",
    "7)": "reddit_voice_pack",
    "8)": "prompt_assets"
}

def normalize(text):
    return re.sub(r"\s+", " ", text.strip())

doc = Document(INPUT_PATH)

data = {}
current_character = None
current_section = None
current_subheader = None

for para in doc.paragraphs:
    text = normalize(para.text)
    if not text:
        continue

    # Detect character header
    if text in CHARACTERS:
        current_character = text
        data[current_character] = {}
        current_section = None
        current_subheader = None
        continue

    if not current_character:
        continue

    # Detect numbered section headers
    for key, section_name in SECTION_MAP.items():
        if text.startswith(key):
            current_section = section_name
            data[current_character][current_section] = {}
            current_subheader = None
            break
    else:
        # Detect subheaders (ends with colon)
        if text.endswith(":"):
            current_subheader = text[:-1]
            data[current_character][current_section][current_subheader] = []
        else:
            # Normal content
            if current_section is None:
                continue

            if current_subheader:
                data[current_character][current_section][current_subheader].append(text)
            else:
                data[current_character][current_section].setdefault("_content", []).append(text)

# Write output files
for character, content in data.items():
    filename = character.lower().replace(" ", "_") + ".json"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w") as f:
        json.dump(
            {
                "character": character,
                "source": "Saving_Nora_CHARACTER VOICE & PERSONA BIBLE.docx",
                "scope": "EP001-100",
                "data": content
            },
            f,
            indent=2,
            ensure_ascii=False
        )
