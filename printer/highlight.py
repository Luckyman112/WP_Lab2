"""Server-side highlighting with Pygments, split into balanced per-line HTML."""
import re

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer

LANGUAGES = {
    'python': 'Python',
    'javascript': 'JavaScript',
    'typescript': 'TypeScript',
    'html': 'HTML',
    'css': 'CSS',
    'c': 'C',
    'cpp': 'C++',
    'java': 'Java',
    'csharp': 'C#',
    'go': 'Go',
    'rust': 'Rust',
    'sql': 'SQL',
    'bash': 'Shell',
    'json': 'JSON',
    'text': 'Plain text',
}

# Pygments' own guess_lexer() is unreliable on short snippets, so detection
# counts telltale patterns instead. The highest score wins, ties go to the
# language listed first.
HINTS = {
    'python': [r'^\s*def \w+\(.*\)\s*(->.*)?:', r'^\s*(from \w[\w.]* )?import \w+', r'^\s*class \w+.*:\s*$',
               r'\bself\.', r'\bprint\(', r'^\s*elif\b', r'\bNone\b'],
    'typescript': [r':\s*(string|number|boolean|void)\b', r'\binterface \w+\s*\{', r'\btype \w+ ='],
    'javascript': [r'\b(const|let) \w+\s*=', r'\bfunction\b\s*\w*\(', r'=>', r'console\.log', r'\bdocument\.'],
    'html': [r'<!doctype html', r'<(div|span|p|a|body|head)\b', r'</\w+>'],
    'css': [r'^[\w.#\-\s,:>*]+\{\s*$', r'^\s*[a-z-]+:\s*[^;{]+;\s*$', r'@media\b'],
    'cpp': [r'#include <(iostream|vector|string|map)>', r'\bstd::', r'\bcout\s*<<'],
    'c': [r'#include <\w+\.h>', r'\bprintf\(', r'\bint main\s*\('],
    'java': [r'public static void main', r'System\.out\.', r'\bpublic (final )?class\b'],
    'csharp': [r'^using System', r'Console\.Write', r'^\s*namespace \w+'],
    'go': [r'^package \w+', r'\bfunc \w*\(', r':=', r'\bfmt\.'],
    'rust': [r'\bfn \w+\(', r'\blet mut\b', r'\w+!\(', r'\bimpl\b'],
    'sql': [r'(?i)\bselect\b[\s\S]+?\bfrom\b', r'(?i)\bcreate table\b', r'(?i)\binsert into\b', r'(?i)\bwhere\b'],
    'bash': [r'^#!/(usr/)?bin/(env )?(ba)?sh', r'^\s*echo\b', r'^\s*(fi|done|esac)\s*$', r'\$\{?\w+\}?'],
    'json': [r'^\s*[\[{]\s*$', r'^\s*"[^"]+"\s*:'],
}
HINTS = {lang: [re.compile(p, re.M) for p in patterns] for lang, patterns in HINTS.items()}


def guess_language(code):
    best, best_score = 'text', 0
    for language, patterns in HINTS.items():
        score = sum(1 for p in patterns if p.search(code))
        if score > best_score:
            best, best_score = language, score
    return best


def render_lines(code, language='auto'):
    """Return highlighted HTML lines plus the language actually used."""
    detected = language == 'auto'
    if detected:
        language = guess_language(code)

    options = {'stripnl': False, 'ensurenl': False, 'tabsize': 4}
    lexer = TextLexer(**options) if language == 'text' else get_lexer_by_name(language, **options)

    # With nowrap=True the formatter closes and reopens spans at every newline,
    # so each line is valid HTML on its own and can be swapped independently.
    html = highlight(code, lexer, HtmlFormatter(nowrap=True))
    lines = html.split('\n')
    wanted = code.count('\n') + 1
    lines = (lines + [''] * wanted)[:wanted]

    return {
        'lines': lines,
        'language': language,
        'label': LANGUAGES[language],
        'detected': detected,
    }
