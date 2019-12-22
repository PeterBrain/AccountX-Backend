from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from . import views
from django.conf.urls import url
router = routers.DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'bookings', views.BookingViewSet)
router.register(r'bookingTypes', views.BookingTypeViewSet)
router.register(r'users',views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
urlpatterns = [
    path('', include(router.urls)),
    url(r'^media$', views.FileUploadView.as_view()),
    path('media/<int:pk>', views.media_download),
    path('media/<int:pk>/get', views.media_get),
]
