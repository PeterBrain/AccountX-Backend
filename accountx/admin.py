from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from . import models

"""
All Admin pages are enabled, although they should not be necessary since all operations can be done through the REST API. 
"""


class CompanyAdmin(GuardedModelAdmin):
    pass


class SaleAdmin(GuardedModelAdmin):
    pass


class PurchaseAdmin(GuardedModelAdmin):
    pass


class MediaAdmin(GuardedModelAdmin):
    pass


admin.site.register(models.Company, CompanyAdmin)

admin.site.register(models.Sale, SaleAdmin)

admin.site.register(models.Purchase, PurchaseAdmin)

admin.site.register(models.Media, MediaAdmin)
