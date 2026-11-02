import json

from django.contrib.staticfiles import finders
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .highlight import LANGUAGES, render_lines
from .models import Printout

MAX_CODE = 20_000

SAMPLE = '''# lp1170.py - feed a file to the line printer, 132 columns wide
import textwrap
from pathlib import Path

COLUMNS = 132
FORM_LENGTH = 66  # lines per page on 11" fanfold paper


def paginate(text: str, width: int = COLUMNS):
    """Split text into pages that fit one sheet of fanfold paper."""
    lines = []
    for raw in text.splitlines():
        lines.extend(textwrap.wrap(raw, width) or [""])
    for start in range(0, len(lines), FORM_LENGTH):
        yield lines[start:start + FORM_LENGTH]


if __name__ == "__main__":
    source = Path(__file__).read_text(encoding="utf-8")
    for number, page in enumerate(paginate(source), start=1):
        print(f"--- page {number} ---")
        print("\\n".join(page))
'''


def _read_json(request):
    try:
        data = json.loads(request.body)
    except ValueError:
        return None
    language = data.get('language', 'auto')
    if language != 'auto' and language not in LANGUAGES:
        language = 'auto'
    return {
        'code': str(data.get('code', ''))[:MAX_CODE],
        'language': language,
        'title': str(data.get('title', '')).strip()[:80],
    }


def index(request, slug=None):
    printout = get_object_or_404(Printout, slug=slug) if slug else None
    if printout:
        result = render_lines(printout.code, printout.language)
        code, chosen = printout.code, printout.language
    else:
        result = render_lines(SAMPLE)
        code, chosen = SAMPLE, 'auto'

    return render(request, 'printer/index.html', {
        'printout': printout,
        'code': code,
        'chosen': chosen,
        'result': result,
        'languages': LANGUAGES,
        'filed': Printout.objects.all()[:8],
        'today': timezone.localtime(),
    })


@require_POST
def highlight_code(request):
    data = _read_json(request)
    if data is None:
        return HttpResponseBadRequest('Expected JSON')
    return JsonResponse(render_lines(data['code'], data['language']))


@require_POST
def file_printout(request):
    data = _read_json(request)
    if data is None:
        return HttpResponseBadRequest('Expected JSON')
    if not data['code'].strip():
        return JsonResponse({'error': 'Nothing to print.'}, status=400)

    language = render_lines(data['code'], data['language'])['language']
    printout = Printout.objects.create(code=data['code'], language=language, title=data['title'])
    return JsonResponse({'url': reverse('printout', args=[printout.slug])})


def download(request, slug):
    printout = get_object_or_404(Printout, slug=slug)
    with open(finders.find('printer/paper.css'), encoding='utf-8') as fh:
        css = fh.read()

    response = render(request, 'printer/export.html', {
        'printout': printout,
        'result': render_lines(printout.code, printout.language),
        'css': css,
    })
    response['Content-Disposition'] = f'attachment; filename="job-{printout.job_number}.html"'
    return response
