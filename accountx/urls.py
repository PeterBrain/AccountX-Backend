from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from . import views
from django.conf.urls import url
router = routers.DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'sales', views.SaleViewSet)
router.register(r'purchases', views.PurchaseViewSet)
router.register(r'bookingTypes', views.BookingTypeViewSet)
router.register(r'users',views.UserViewSet, basename="users")
router.register(r'ustReport',views.UstReportViewset, basename="ustreport")
router.register(r'groups', views.GroupViewSet, basename="groups")
urlpatterns = [
    path('', include(router.urls)),
    url(r'^media$', views.FileUploadView.as_view()),
    path('media/<int:pk>', views.media_download),
    path('media/<int:pk>/get', views.media_get),
]
