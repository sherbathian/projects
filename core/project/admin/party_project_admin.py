from django.contrib import admin
from project.models import ProjectParty

# Admin for ProjectParty
@admin.register(ProjectParty)
class ProjectPartyAdmin(admin.ModelAdmin):
    list_display = ('project', 'party', 'share')
    list_filter = ('project', 'party')
