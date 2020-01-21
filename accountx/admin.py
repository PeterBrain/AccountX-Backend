from django.contrib import admin

from guardian.admin import GuardedModelAdmin
from . import models

# Register your models here.


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
