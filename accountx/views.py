from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from rest_framework import exceptions, viewsets
from rest_framework.decorators import api_view
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models, permissions, serializers


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = models.Company.objects.all()
    serializer_class = serializers.CompanySerializer

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [IsAuthenticated]
        elif self.action == "retrieve":
            permission_classes = [
                (permissions.IsOwner | permissions.IsAccountant) & IsAuthenticated]
        else:
            permission_classes = [
                (permissions.IsOwner) & IsAuthenticated]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, pk=None):
        queryset = models.Company.objects.all()
        company = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, company)
        return Response(serializers.CompanySerializer(company).data)

    def list(self, request):
        if request.user.is_superuser:
            queryset = models.Company.objects.all()
        else:
            queryset = models.Company.objects.filter(
                Q(admins=request.user.id) | Q(accountants=request.user.id))
            self.check_object_permissions(self.request, queryset)
        return Response(serializers.CompanySerializer(queryset, many=True).data)


class BookingViewSet(viewsets.ModelViewSet):
    queryset = models.Booking.objects.all()
    serializer_class = serializers.BookingSerializer

    def list(self, request):
        if request.user.is_superuser:
            queryset = models.Booking.objects.all()
        else:
            queryset = models.Booking.objects.filter(
                Q(company__admins=request.user.id) | Q(company__accountants=request.user.id))
        if(self.request.GET.get('cid')):
            queryset = queryset.filter(company__id=self.request.GET.get('cid'))
        return Response(serializers.BookingSerializer(queryset, many=True).data)


class BookingTypeViewSet(viewsets.ModelViewSet):
    queryset = models.BookingType.objects.all()
    serializer_class = serializers.BookingTypeSerializer
    permission_classes = [permissions.IsOwner & IsAuthenticated]

    def list(self, request):
        if request.user.is_superuser:
            queryset = models.BookingType.objects.all()
        else:
            queryset = models.BookingType.objects.filter(
                Q(company__admins=request.user.id) | Q(company__accountants=request.user.id))
        if(self.request.GET.get('cid')):
            queryset = queryset.filter(company__id=self.request.GET.get('cid'))
        return Response(serializers.BookingTypeSerializer(queryset, many=True).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [IsAdminUser]
        elif self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


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
