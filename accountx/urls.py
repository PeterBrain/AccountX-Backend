from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'sales', views.SaleViewSet)
router.register(r'purchases', views.PurchaseViewSet)
router.register(r'users', views.UserViewSet, basename="users")
router.register(r'vatReport', views.VatReportViewset, basename="vatreport")
router.register(r'groups', views.GroupViewSet, basename="groups")
router.register(r'media', views.MediaViewSet, basename="media")
urlpatterns = [
    path('', include(router.urls)),
]
