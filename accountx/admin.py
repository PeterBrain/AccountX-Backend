from django.contrib import admin

from guardian.admin import GuardedModelAdmin
from . import models

# Register your models here.


class CompanyAdmin(GuardedModelAdmin):
    pass


admin.site.register(models.Company, CompanyAdmin)
