import re
from pathlib import Path


def parse_costumes(filepath=None):
    if filepath is None:
        filepath = Path(__file__).parent / "costume_prompts.md"

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    categories = []

    # Split by category headers (## )
    category_sections = re.split(r'^## ', content, flags=re.MULTILINE)

    for cat_idx, section in enumerate(category_sections[1:]):  # Skip preamble
        lines = section.split('\n')
        category_header = lines[0].strip()  # e.g. "📜 פורים קלאסי"

        # Extract emoji and name: first whitespace-delimited token = emoji
        parts = category_header.split(' ', 1)
        if len(parts) >= 2:
            category_emoji = parts[0]
            category_name = parts[1]
        else:
            category_emoji = ''
            category_name = category_header

        # Get all costume sections within this category
        category_content = '\n'.join(lines[1:])
        costume_sections = re.split(r'^### ', category_content, flags=re.MULTILINE)

        costumes = []
        for cos_idx, costume_section in enumerate(costume_sections[1:]):
            cos_lines = costume_section.split('\n')
            costume_header = cos_lines[0].strip()

            # Parse header: "EMOJI English Name | Hebrew Name"
            if '|' in costume_header:
                before_pipe, after_pipe = costume_header.split('|', 1)
                hebrew_name = after_pipe.strip()
                before_stripped = before_pipe.strip()
                words = before_stripped.split()
                if words:
                    costume_emoji = words[0]
                    english_name = ' '.join(words[1:])
                else:
                    costume_emoji = ''
                    english_name = before_stripped
            else:
                costume_header_stripped = costume_header.strip()
                words = costume_header_stripped.split()
                costume_emoji = words[0] if words else ''
                english_name = ' '.join(words[1:]) if len(words) > 1 else costume_header_stripped
                hebrew_name = english_name

            # Get prompt text: everything after header line up to "---"
            prompt_lines = []
            for line in cos_lines[1:]:
                if line.strip() == '---':
                    break
                prompt_lines.append(line)

            prompt = '\n'.join(prompt_lines).strip()

            if prompt:
                costumes.append({
                    'id': f"cat{cat_idx}_cos{cos_idx}",
                    'emoji': costume_emoji,
                    'english_name': english_name,
                    'hebrew_name': hebrew_name,
                    'prompt': prompt,
                })

        if costumes:
            categories.append({
                'id': f"cat{cat_idx}",
                'emoji': category_emoji,
                'name': category_name,
                'costumes': costumes,
            })

    return categories


if __name__ == '__main__':
    cats = parse_costumes()
    total = 0
    for cat in cats:
        print(f"\n{cat['emoji']} {cat['name']} ({len(cat['costumes'])} costumes)")
        for c in cat['costumes']:
            print(f"  {c['emoji']} {c['hebrew_name']}")
        total += len(cat['costumes'])
    print(f"\nTotal: {total} costumes in {len(cats)} categories")
