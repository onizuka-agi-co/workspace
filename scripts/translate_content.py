#!/usr/bin/env python3
"""
Auto-translate markdown content for AGI Knowledge Hub i18n.
Usage:
  python3 scripts/translate_content.py --input <file> --lang en
  python3 scripts/translate_content.py --input <file> --lang zh
  python3 scripts/translate_content.py --dir memory/docs/2026/05 --lang en
"""
import argparse
import json
import os
import re
import sys

# Add .pip to path for deep-translator
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.pip'))

from deep_translator import GoogleTranslator

LANG_MAP = {
    'en': 'en',
    'zh': 'zh-CN',
    'zh-CN': 'zh-CN',
    'zh-TW': 'zh-TW',
}

def translate_text(text, target_lang='en'):
    """Translate text using Google Translate."""
    if not text or not text.strip():
        return text
    dest = LANG_MAP.get(target_lang, target_lang)
    try:
        translator = GoogleTranslator(source='auto', target=dest)
        # Split long text into chunks (Google limit ~5000 chars)
        if len(text) > 4500:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            return '\n'.join(translator.translate(chunk) for chunk in chunks)
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}", file=sys.stderr)
        return text

def process_markdown(content, target_lang='en'):
    """Translate markdown content while preserving structure."""
    lines = content.split('\n')
    result = []
    in_frontmatter = False
    in_code_block = False

    for line in lines:
        # Handle code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue
        if in_code_block:
            result.append(line)
            continue

        # Handle frontmatter
        if line.strip() == '---' and not in_frontmatter and len(result) < 5:
            in_frontmatter = True
            result.append(line)
            continue
        if in_frontmatter:
            if line.strip() == '---':
                in_frontmatter = False
            # Translate title field in frontmatter
            if line.startswith('title:'):
                title = line.replace('title:', '').strip().strip('"').strip("'")
                translated = translate_text(title, target_lang)
                result.append(f'title: "{translated}"')
            else:
                result.append(line)
            continue

        # Skip empty lines, headers structure
        if not line.strip():
            result.append(line)
            continue

        # Translate regular text
        translated = translate_text(line, target_lang) or line
        result.append(translated)

    return '\n'.join(result)

def translate_file(input_path, target_lang='en', output_path=None):
    """Translate a single markdown file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    translated = process_markdown(content, target_lang)

    if output_path is None:
        # Auto-generate output path: memory/docs/... -> memory/docs/{lang}/...
        parts = input_path.split('/')
        # Find 'docs' in path and insert lang after it
        for i, p in enumerate(parts):
            if p == 'docs':
                parts.insert(i + 1, target_lang)
                break
        output_path = '/'.join(parts)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated)

    print(f"Translated: {input_path} -> {output_path}")
    return output_path

def translate_directory(dir_path, target_lang='en', pattern='*.md'):
    """Translate all markdown files in a directory."""
    import glob
    files = glob.glob(os.path.join(dir_path, '**', pattern), recursive=True)
    # Exclude already translated directories
    files = [f for f in files if f'/{target_lang}/' not in f]

    translated = []
    for f in sorted(files):
        try:
            out = translate_file(f, target_lang)
            translated.append(out)
        except Exception as e:
            print(f"Error translating {f}: {e}", file=sys.stderr)

    print(f"\nTranslated {len(translated)}/{len(files)} files to {target_lang}")
    return translated

def main():
    parser = argparse.ArgumentParser(description='Translate markdown content for i18n')
    parser.add_argument('--input', '-i', help='Input markdown file')
    parser.add_argument('--dir', '-d', help='Input directory')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--lang', '-l', required=True, choices=['en', 'zh', 'zh-CN', 'zh-TW'],
                        help='Target language')
    parser.add_argument('--pattern', default='*.md', help='File pattern for directory mode')
    args = parser.parse_args()

    if args.input:
        translate_file(args.input, args.lang, args.output)
    elif args.dir:
        translate_directory(args.dir, args.lang, args.pattern)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
