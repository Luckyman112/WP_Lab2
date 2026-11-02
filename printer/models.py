import secrets

from django.db import models


def make_slug():
    return secrets.token_hex(3)


class Printout(models.Model):
    """A highlighted listing that was torn off and filed."""

    slug = models.SlugField(max_length=12, unique=True, default=make_slug)
    title = models.CharField(max_length=80, blank=True)
    language = models.CharField(max_length=20)
    code = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.title or f'Job {self.job_number}'

    @property
    def job_number(self):
        return f'{self.pk:04d}'
