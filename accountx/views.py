from urllib import request

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from guardian.shortcuts import (assign_perm, get_objects_for_group,
                                get_objects_for_user)
from rest_framework import exceptions, viewsets
from rest_framework.decorators import api_view
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models, serializers


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = models.Company.objects.all()
    serializer_class = serializers.CompanySerializer

    def list(self, request):
        queryset = get_objects_for_user(
            request.user, "view_company", any_perm=True, klass=models.Company)
        return Response(serializers.CompanySerializer(queryset, many=True).data)

    def retrieve(self, request, pk=None):
        queryset = get_objects_for_user(
            request.user, "change_company", any_perm=True, klass=models.Company)
        company = get_object_or_404(queryset, pk=pk)
        return Response(serializers.CompanySerializer(company).data)

    def perform_create(self, serializer):
        obj = serializer.save()
        admins = Group.objects.create(name=obj.name+'_admins')
        accountants = Group.objects.create(name=obj.name+'_accountants')
        self.request.user.groups.add(admins)
        self.request.user.groups.add(accountants)
        assign_perm("change_company", admins, obj)
        assign_perm("view_company", admins, obj)
        assign_perm("delete_company", admins, obj)
        assign_perm("change_group", admins, admins)
        assign_perm("change_group", admins, accountants)
        assign_perm("view_company", accountants, obj)


class BookingViewSet(viewsets.ModelViewSet):
    queryset = models.Booking.objects.all()
    serializer_class = serializers.BookingSerializer

    def list(self, request):
        queryset = get_objects_for_user(
            request.user, "view_booking", klass=models.Booking)
        if(self.request.GET.get('cid')):
            queryset = queryset.filter(company__id=self.request.GET.get('cid'))
        return Response(serializers.BookingSerializer(queryset, many=True).data)

    def perform_create(self, serializer):
        obj = serializer.save()
        admins = Group.objects.get(name=obj.company.name+'_admins')
        accountants = Group.objects.get(name=obj.company.name+'_accountants')
        assign_perm("change_booking", admins, obj)
        assign_perm("view_booking", admins, obj)
        assign_perm("delete_booking", admins, obj)
        assign_perm("change_booking", accountants, obj)
        assign_perm("view_booking", accountants, obj)
        assign_perm("delete_booking", accountants, obj)

    def retrieve(self, request, pk=None):
        queryset = get_objects_for_user(
            request.user, "change_booking", any_perm=True, klass=models.Booking)
        company = get_object_or_404(queryset, pk=pk)
        return Response(serializers.BookingSerializer(company).data)


class BookingTypeViewSet(viewsets.ModelViewSet):
    queryset = models.BookingType.objects.all()
    serializer_class = serializers.BookingTypeSerializer

    def list(self, request):
        queryset = get_objects_for_user(
            request.user, "view_bookingtype", any_perm=True, klass=models.BookingType)
        if(self.request.GET.get('cid')):
            queryset = queryset.filter(company__id=self.request.GET.get('cid'))
        return Response(serializers.BookingTypeSerializer(queryset, many=True).data)

    def perform_create(self, serializer):
        obj = serializer.save()
        admins = Group.objects.get(name=obj.company.name+'_admins')
        accountants = Group.objects.get(name=obj.company.name+'_accountants')
        assign_perm("change_bookingtype", admins, obj)
        assign_perm("view_bookingtype", admins, obj)
        assign_perm("delete_bookingtype", admins, obj)
        assign_perm("view_bookingtype", accountants, obj)

    def retrieve(self, request, pk=None):
        queryset = get_objects_for_user(
            request.user, "view_bookingtype", any_perm=True, klass=models.BookingType)
        company = get_object_or_404(queryset, pk=pk)
        return Response(serializers.BookingTypeSerializer(company).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    def list(self, request):
        queryset = User.objects.filter(groups__in=request.user.groups.all())
        return Response(serializers.UserSerializer(queryset, many=True).data)

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return serializers.UserSerializer
        else:
            return serializers.RegisterUserSerializer


class FileUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        file = request.FILES['file']
        file_input = {
            'original_file_name': file.name,
            'content_type': file.content_type,
            'size': file.size,
        }
        serializer = serializers.MediaSerializer(data=file_input)
        if serializer.is_valid():
            serializer.save()
            default_storage.save(
                'media/' + str(serializer.data['id']), ContentFile(file.read()))
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


def media_download(request, pk):
    media = models.Media.objects.get(pk=pk)
    data = default_storage.open('media/' + str(pk)).read()
    content_type = media.content_type
    response = HttpResponse(data, content_type=content_type)
    original_file_name = media.original_file_name
    response['Content-Disposition'] = 'inline; filename=' + original_file_name
    return response


@api_view(['GET'])
def media_get(request, pk):
    try:
        media = models.Booking.objects.get(pk=pk)
    except models.Booking.DoesNotExist:
        return Response({'error': 'Media does not exist.'}, status=404)

    serializer = serializers.MediaSerializer(media)
    return Response(serializer.data)
