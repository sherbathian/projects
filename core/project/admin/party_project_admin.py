from django.contrib import admin
from project.models import ProjectParty
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

class ProjectPartyResource(resources.ModelResource):

    class Meta:
        fields = ('project__name', 'party__name', 'share')
        model = ProjectParty

# Admin for ProjectParty
@admin.register(ProjectParty)
class ProjectPartyAdmin(ExportActionMixin, ImportExportModelAdmin):
    resource_class = ProjectPartyResource
    list_display = ('project', 'party', 'share')
    list_filter = ('project', 'party')
