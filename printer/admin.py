from django.contrib import admin

from .models import Printout


@admin.register(Printout)
class PrintoutAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'title', 'language', 'created')
    search_fields = ('title', 'code')
