from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from guardian.shortcuts import (get_groups_with_perms, get_objects_for_user,
                                get_users_with_perms)
from rest_framework import viewsets
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_guardian import filters as guardianFilters

from . import models, serializers


class SaleFilter(filters.FilterSet):
    """
    Provides filtering for sales depending on the dates.
    """
    cashflowdate = filters.DateFromToRangeFilter('cashflowdate')
    invDate = filters.DateFromToRangeFilter('invDate')

    class Meta:
        model = models.Sale
        fields = ('company', 'cashflowdate', 'invDate')


class UserFilter(filters.FilterSet):
    """
    Provides filtering for users based on the companies they can view.
    """
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
    """
    Provides filtering for groups based on the companies they can view.
    """
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
    """
    Provides filtering for purchases depending on the dates.
    """
    cashflowdate = filters.DateFromToRangeFilter('cashflowdate')
    invDate = filters.DateFromToRangeFilter('invDate')

    class Meta:
        model = models.Purchase
        fields = ('company', 'cashflowdate', 'invDate')


class CompanyViewSet(viewsets.ModelViewSet):
    """
    A viewset for the companies.
    """
    queryset = models.Company.objects.all()
    serializer_class = serializers.CompanySerializer
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]


class SaleViewSet(viewsets.ModelViewSet):
    """
    A viewset for the sales.
    """
    queryset = models.Sale.objects.all()
    serializer_class = serializers.SaleSerializer
    filterset_class = SaleFilter
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]


class VatReportViewset(viewsets.ViewSet):
    """
    A viewset for the vat report.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.VatReportSerializer

    def list(self, request):
        """
        This calculates the vat (for sales and for purchases) for a company within
        a specified time range. It also checks for the necessary permissions.
        """
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
        vatIn = sum(sale.vat * sale.net for sale in sales)
        vatOut = sum(purchase.vat * purchase.net for purchase in purchases)
        outData = [{"company": cid, "vatIn": vatIn, "vatOut": vatOut}]
        results = serializers.VatReportSerializer(
            instance=outData, many=True).data
        return Response(results)


class PurchaseViewSet(viewsets.ModelViewSet):
    """
    A viewset for the purchases.
    """
    queryset = models.Purchase.objects.all()
    serializer_class = serializers.PurchaseSerializer
    filterset_class = PurchaseFilter
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]


class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for the sales.
    """
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    filterset_class = UserFilter
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]

    def get_permissions(self):
        """
        This ensures that any user can create an user (register).
        """
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        This returnes the register view if the client is an anonymous user and
        the create user view for admins.
        """
        if self.request.user.is_authenticated:
            return serializers.UserSerializer
        else:
            return serializers.RegisterUserSerializer


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for groups
    """
    serializer_class = serializers.GroupSerializer
    filterset_class = GroupFilter

    def get_queryset(self):
        """
        This ensures that the user can only see groups he is able to change.
        """
        return get_objects_for_user(self.request.user, "change_group", klass=Group)


class MediaViewSet(viewsets.ModelViewSet):
    """
    A viewset for medias.
    The metadata for the media can be retrieved by filtering the list view.
    """
    parser_classes = [MultiPartParser]
    serializer_class = serializers.MediaSerializer
    queryset = models.Media.objects.all()
    filterset_fields = ['company', 'id']
    filter_backends = [filters.DjangoFilterBackend,
                       guardianFilters.ObjectPermissionsFilter]

    def create(self, request, format=None):
        """
        Implements the file upload functionality.
        """
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
        """
        Implements the file download functionality
        """
        media = models.Media.objects.get(pk=pk)
        data = default_storage.open('media/' + str(pk)).read()
        content_type = media.content_type
        response = HttpResponse(data, content_type=content_type)
        original_file_name = media.original_file_name
        response['Content-Disposition'] = 'inline; filename=' + \
                                          original_file_name
        return response
