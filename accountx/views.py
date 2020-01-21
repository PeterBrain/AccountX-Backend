from urllib import request

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django_filters import rest_framework as filters
from guardian.shortcuts import (assign_perm, get_groups_with_perms,
                                get_objects_for_group, get_objects_for_user,
                                get_users_with_perms)
from rest_framework import exceptions, viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_guardian import filters as guardianFilters

from accountx.views import User

from . import models, serializers


class SaleFilter(filters.FilterSet):
    cashflowdate = filters.DateFromToRangeFilter('cashflowdate')
    invDate = filters.DateFromToRangeFilter('invDate')

    class Meta:
        model = models.Sale
        fields = ('company', 'cashflowdate', 'invDate')


class UserFilter(filters.FilterSet):
    cid = filters.NumberFilter(method='filter_companies', label='cid')

    def filter_companies(self, queryset, name, value):
        company = get_objects_for_user(
            self.request.user, "view_company", klass=models.Company).filter(pk=value)
        if company.exists():
            return get_users_with_perms(company.first())
        else:
            return User.objects.none()

    class Meta:
        model = User
        fields = ['cid']


class GroupFilter(filters.FilterSet):
    cid = filters.NumberFilter(method='filter_companies', label='cid')

    def filter_companies(self, queryset, name, value):
        company = get_objects_for_user(
            self.request.user, "view_company", klass=models.Company).filter(pk=value)
        if company.exists():
            return get_groups_with_perms(company.first())
        else:
            return Group.objects.none()

    class Meta:
        model = Group
        fields = ['cid']


class PurchaseFilter(filters.FilterSet):
    cashflowdate = filters.DateFromToRangeFilter('cashflowdate')
    invDate = filters.DateFromToRangeFilter('invDate')

    class Meta:
        model = models.Purchase
        fields = ('company', 'cashflowdate', 'invDate')


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = models.Company.objects.all()
    serializer_class = serializers.CompanySerializer
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]


class SaleViewSet(viewsets.ModelViewSet):
    queryset = models.Sale.objects.all()
    serializer_class = serializers.SaleSerializer
    filterset_class = SaleFilter
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]


class VatReportViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.VatReportSerializer

    def list(self, request):
        before = request.query_params.get("before")
        after = request.query_params.get("after")
        cid = request.query_params.get("cid")
        if (cid is None or before is None or after is None):
            raise APIException(detail="Url parameters missing")
        company = get_object_or_404(models.Company, pk=cid)
        if (not request.user.has_perm("view_company", company)):
            raise PermissionDenied
        sales = models.Sale.objects.filter(
            company=company, cashflowdate__range=[after, before])
        purchases = models.Purchase.objects.filter(
            company=company, cashflowdate__range=[after, before])
        vatIn = sum(sale.vat*sale.net for sale in sales)
        vatOut = sum(purchase.vat*purchase.net for purchase in purchases)
        outData = [{"company": cid, "vatIn": vatIn, "vatOut": vatOut}]
        results = serializers.VatReportSerializer(
            instance=outData, many=True).data
        return Response(results)


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = models.Purchase.objects.all()
    serializer_class = serializers.PurchaseSerializer
    filterset_class = PurchaseFilter
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    filterset_class = UserFilter
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]

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


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.GroupSerializer
    filterset_class = GroupFilter

    def get_queryset(self):
        return get_objects_for_user(self.request.user, "change_group", klass=Group)


class MediaViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser]
    serializer_class = serializers.MediaSerializer
    queryset = models.Media.objects.all()
    filterset_fields = ['company', 'id']
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]

    def create(self, request, format=None):
        file = request.FILES['file']
        file_input = {'original_file_name': file.name,
                      'content_type': file.content_type, 'size': file.size, 'company': request.POST.get('company')}
        serializer = serializers.MediaSerializer(
            data=file_input, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            default_storage.save(
                'media/' + str(serializer.data['id']), ContentFile(file.read()))
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def retrieve(self, request, pk):
        media = models.Media.objects.get(pk=pk)
        data = default_storage.open('media/' + str(pk)).read()
        content_type = media.content_type
        response = HttpResponse(data, content_type=content_type)
        original_file_name = media.original_file_name
        response['Content-Disposition'] = 'inline; filename=' + \
            original_file_name
        return response
