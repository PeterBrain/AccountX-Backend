from rest_framework.permissions import BasePermission
from . import models


class IsAccountant(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, models.Company):
            return request.user in obj.accountants.all()

        else:
            return request.user in obj.company.accountants.all()


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, models.Company):
            return request.user in obj.admins.all()
        else:
            return request.user in obj.company.admins.all()
