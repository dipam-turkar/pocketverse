
import docx
import json
import os
import re

def clean_text(text):
    return text.strip().replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')

def is_character_header(text, known_characters):
    clean = clean_text(text).upper()
    return clean in known_characters

def is_section_header(text):
    # Matches "1) ", "2) " etc.
    return re.match(r'^\d+\)\s+.*', text)

def extract_data(docx_path, output_dir):
    doc = docx.Document(docx_path)
    
    # Pre-define known characters from the inspection or logic
    # The document listed: NORA SMITH • JUSTIN HUNT • HENRY SMITH
    # We can also dynamically find them if we want, but hardcoding for this specific bible is safer if we know them.
    # However, let's try to be slightly dynamic or at least generous.
    known_characters = ["NORA SMITH", "JUSTIN HUNT", "HENRY SMITH"]
    
    characters = {}
    current_char = None
    current_section = None
    current_subsection = None
    buffer_text = [] # To accumulate multi-paragraph values if needed
    
    # Helper to flush buffer
    def flush_buffer():
        nonlocal buffer_text, current_char, current_section, current_subsection
        # log_msg(f"Flushing buffer... {len(buffer_text)} items. Char: {current_char}, Sect: {current_section}")
        if not buffer_text:
            return
        
        content = "\n".join(buffer_text).strip()
        if not content:
            return

        if current_char and current_section:
            if current_subsection:
                if current_subsection not in characters[current_char][current_section]:
                     characters[current_char][current_section][current_subsection] = content
                     log_msg(f"Saved subsection: {current_element_summary(current_subsection)}")
                else:
                     characters[current_char][current_section][current_subsection] += "\n" + content
                     log_msg(f"Appended subsection: {current_element_summary(current_subsection)}")
            else:
                if "content" not in characters[current_char][current_section]:
                    characters[current_char][current_section]["content"] = []
                characters[current_char][current_section]["content"].append(content)
                log_msg(f"Saved content to section: {current_element_summary(current_section)}")
        else:
            log_msg("Skipped flush: No Char/Sect")
        
        buffer_text = []

    def log_msg(msg):
        with open("debug_log.txt", "a") as f:
            f.write(msg + "\n")
            
    def current_element_summary(el):
        return str(el)[:20] if el else "None"

    # clear log
    with open("debug_log.txt", "w") as f:
        f.write("Starting Debug\n")

    para_count = 0
    for para in doc.paragraphs:
        para_count += 1
        text = clean_text(para.text)
        if not text:
            continue
            
        if para_count < 200:
             log_msg(f"L{para_count}: {text[:40]}")
            
        # Check for Character Header
        if text.upper() in known_characters:
            flush_buffer()
            current_char = text.upper()
            if current_char not in characters:
                characters[current_char] = {}
                print(f"New Character Found: {current_char}")
            else:
                print(f"Refinding Character: {current_char} (Merging/Appending)")
            
            # We don't necessarily want to reset sections if we are merging, 
            # but usually a new header means a new block. 
            # Let's keep sections cumulative.
            current_section = None
            current_subsection = None
            continue
            
        if not current_char:
            continue

            
        # Check for Section Header (1) ..., 2) ...)
        # Check for Section Header (1) ..., 2) ...)
        if is_section_header(text):
            flush_buffer()
            current_section = text
            if current_section not in characters[current_char]:
                characters[current_char][current_section] = {}
                log_msg(f"NEW SECTION: {current_section}")
            else:
                log_msg(f"REFIND SECTION: {current_section}")
            current_subsection = None
            continue
            
        if is_section_header(text) is False and current_section:
            # Inside a section
            
            # Check for Key: Value
            if ":" in text:
                parts = text.split(":", 1)
                key = parts[0].strip()
                val = parts[1].strip()
                
                if len(key) < 50:
                    flush_buffer()
                    characters[current_char][current_section][key] = val
                    log_msg(f"KV ADD: {key} -> {val[:10]}")
                    continue
                else:
                    log_msg(f"KV SKIP (Long): {key[:20]}")
            
            # Check for potential sub-header
            if len(text) < 50 and not text.endswith("."):
                flush_buffer()
                current_subsection = text
                log_msg(f"SUBSEC NEW: {current_subsection}")
                continue
                
            # Otherwise, it's body text
            buffer_text.append(text)
            
    flush_buffer()
    
    # Save to JSONs
    for char_name, data in characters.items():
        # Clean filename
        safe_name = char_name.replace(" ", "_").lower()
        file_path = os.path.join(output_dir, f"{safe_name}.json")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {file_path}")

if __name__ == "__main__":
    extract_bible_data_path = "PromoCanon/Saving_Nora_CHARACTER BIBLE.docx"
    output_context_dir = "context"
    extract_data(extract_bible_data_path, output_context_dir)
