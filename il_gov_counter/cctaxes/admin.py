from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import TaxCode, PropAddress

admin.site.register(PropAddress)
#admin.site.register(TaxCode)

# admin.site.register(TaxCode)
# class TaxCodeAdmin(ImportExportModelAdmin):
#     pass
@admin.register(TaxCode)
class TaxCodeAdmin(ImportExportModelAdmin):
    pass
