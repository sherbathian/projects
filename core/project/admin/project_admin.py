from django.contrib import admin
from project.models import Project 
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin


class ProjectResource(resources.ModelResource):

    class Meta:
        fields = ('name', 'status', 'start_date', 'end_date', 'budget')
        model = Project
         
# Admin for Project
@admin.register(Project)
class ProjectAdmin(ExportActionMixin, ImportExportModelAdmin):

    resource_class = ProjectResource
    list_display = ('name', 'status', 'start_date', 'end_date', 'budget')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    # optional: restrict import formats or configure import behavior
    # from import_export.formats import base_formats
    # def get_import_formats(self):
    #     return [f() for f in (base_formats.CSV,

admin.site.site_header = "Project Admin"
admin.site.site_title = "Project Admin"
admin.site.index_title = "Welcome to the Project Admin"   