import json

from django.test import TestCase
from django.urls import reverse

from .highlight import guess_language, render_lines
from .models import Printout


class HighlightTests(TestCase):
    def test_one_html_line_per_source_line(self):
        code = 'x = """a\nb"""\nprint(x)\n'
        result = render_lines(code, 'python')
        self.assertEqual(len(result['lines']), 4)
        # the multi-line string must be closed on each line
        self.assertEqual(result['lines'][0].count('<span'), result['lines'][0].count('</span>'))

    def test_guess(self):
        self.assertEqual(guess_language('def f(x):\n    return x\n'), 'python')
        self.assertEqual(guess_language('SELECT id FROM users WHERE id = 1;'), 'sql')
        self.assertEqual(guess_language('#include <stdio.h>\nint main() { printf("hi"); }'), 'c')
        self.assertEqual(guess_language('just some words'), 'text')

    def test_markup_is_escaped(self):
        result = render_lines('<script>alert(1)</script>', 'text')
        self.assertNotIn('<script>', result['lines'][0])


class ViewTests(TestCase):
    def post(self, name, payload):
        return self.client.post(reverse(name), json.dumps(payload), content_type='application/json')

    def test_index(self):
        self.assertContains(self.client.get(reverse('index')), 'LP-1170')

    def test_highlight_api(self):
        data = self.post('highlight', {'code': 'fn main() { let mut x = 1; }', 'language': 'auto'}).json()
        self.assertEqual(data['language'], 'rust')
        self.assertTrue(data['detected'])

    def test_file_and_download(self):
        url = self.post('file', {'code': 'print(1)', 'language': 'python', 'title': 'demo'}).json()['url']
        printout = Printout.objects.get()
        self.assertContains(self.client.get(url), 'demo')
        response = self.client.get(reverse('download', args=[printout.slug]))
        self.assertIn('attachment', response['Content-Disposition'])

    def test_empty_job_rejected(self):
        self.assertEqual(self.post('file', {'code': '   '}).status_code, 400)
