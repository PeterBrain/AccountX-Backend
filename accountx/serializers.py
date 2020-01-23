from django.contrib.auth.models import Group, Permission, User
from django.shortcuts import get_object_or_404
from guardian.shortcuts import (assign_perm, get_groups_with_perms,
                                get_objects_for_group, get_objects_for_user)
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework_guardian.serializers import \
    ObjectPermissionsAssignmentMixin

from . import models


class CompanySerializer(serializers.ModelSerializer, ObjectPermissionsAssignmentMixin):
    """
    The serializer for the company model.
    """
    groups = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Company
        fields = ['name', 'description', 'groups', 'id']

    def create(self, validated_data):
        """
        This ensures that the groups for the company (admins and accountants) are created
        and assignes the rights accordingly.
        """
        admins = Group.objects.create(
            name=validated_data['name'] + ' Admins')
        accountants = Group.objects.create(
            name=validated_data['name'] + ' Accountants')
        validated_data['accountants'] = accountants
        validated_data['admins'] = admins
        company = super(CompanySerializer, self).create(validated_data)
        company.save()
        return company

    def get_groups(self, obj):
        """
        Returns a list of all groups with any rights on the company.
        """
        groupsForCompany = get_groups_with_perms(obj)
        return [x.id for x in groupsForCompany]

    def get_permissions_map(self, created):
        """
        This function is called by the permission assignment mixin.
        The returned permissions are then assigned on the object.
        """
        current_user = self.context['request'].user
        company = get_object_or_404(models.Company, pk=self.data['id'])
        admins = company.admins
        accountants = company.accountants
        current_user.groups.add(admins)
        current_user.groups.add(accountants)
        assign_perm("change_group", admins, admins)
        assign_perm("change_group", admins, accountants)
        assign_perm("delete_group", admins, admins)
        assign_perm("delete_group", admins, accountants)
        return {
            'view_company': [admins, accountants],
            'change_company': [admins],
            'delete_company': [admins]
        }


class SaleSerializer(serializers.ModelSerializer, ObjectPermissionsAssignmentMixin):
    """
    The serializer for the sales model.
    """
    gross = serializers.SerializerMethodField()
    invNo = serializers.SerializerMethodField()

    class Meta:
        model = models.Sale
        fields = '__all__'

    def get_gross(self, obj):
        """
        This calculates the gross value, since it would be unecessary
        to store this information.
        """
        return obj.net * (1 + obj.vat)

    def get_invNo(self, obj):
        """
        This generates a invoice number.
        """
        return str(obj.invDate.year) + str(obj.id)

    def validate(self, data):
        """
        This is a crude method to ensure that no one can create a sale on
        a foreign company. Or use a foreign invoice.
        """
        company = data['company']
        invoice = data.get("invoice")
        if not self.context['request'].user.has_perm("view_company", company) or not all(self.context['request'].user.has_perm("view_media", media) for media in invoice):
            raise PermissionDenied()
        return data

    def get_permissions_map(self, created):
        """
        This function is called by the permission assignment mixin.
        The returned permissions are then assigned on the object.
        """
        company = get_object_or_404(models.Company, pk=self.data['company'])
        admins = company.admins
        accountants = company.accountants
        return {
            'view_sale': [admins, accountants],
            'change_sale': [admins, accountants],
            'delete_sale': [admins, accountants]
        }


class PurchaseSerializer(serializers.ModelSerializer, ObjectPermissionsAssignmentMixin):
    """
    The serializer for the purchase model.
    """
    gross = serializers.SerializerMethodField()

    class Meta:
        model = models.Purchase
        fields = '__all__'

    def get_gross(self, obj):
        """
        This calculates the gross value, since it would be unecessary
        to store this information.
        """
        return obj.net * (1 + obj.vat)

    def validate(self, data):
        """
        This is a crude method to ensure that no one can create a purchase on
        a foreign company. Or use a foreign invoice.
        """
        company = data['company']
        invoice = data.get("invoice")
        if not self.context['request'].user.has_perm("view_company", company) or not all(self.context['request'].user.has_perm("view_media", media) for media in invoice):
            raise PermissionDenied()
        return data

    def get_permissions_map(self, created):
        """
        This function is called by the permission assignment mixin.
        The returned permissions are then assigned on the object.
        """
        company = get_object_or_404(models.Company, pk=self.data['company'])
        admins = company.admins
        accountants = company.accountants
        return {
            'view_purchase': [admins, accountants],
            'change_purchase': [admins, accountants],
            'delete_purchase': [admins, accountants]
        }


class VatReportSerializer(serializers.Serializer):
    """
    This is a serializer used for calculating the vat within a certain time
    range. It does not belong to a model, instead the values are calculated
    within the view.
    """
    company = serializers.IntegerField()
    vatIn = serializers.FloatField()
    vatOut = serializers.FloatField()


class UserSerializer(serializers.ModelSerializer):
    """
    The serializer for the user model.
    This is only used for authenticated users.
    For the serializer representing data to 
    anonymous users, please see the RegisterUserSerializer.
    """
    password = serializers.CharField(write_only=True, required=False)
    companies = serializers.SerializerMethodField(read_only=True)
    isAdminOf = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password',
                  'first_name', 'last_name', 'groups', 'companies', 'isAdminOf']

    def get_isAdminOf(self, obj):
        """
        This is provides helpful information to the frontend.
        It lists all companies this user can change (is admin of).
        """
        userCompanies = get_objects_for_user(
            obj, "change_company", klass=models.Company, accept_global_perms=False)
        return [x.id for x in userCompanies]

    def get_companies(self, obj):
        """
        This is provides helpful information to the frontend.
        It lists all companies the user is a member of.
        """
        userCompanies = get_objects_for_user(
            obj, "view_company", klass=models.Company)
        return [x.id for x in userCompanies]

    def validate(self, data):
        """
        This is a crude method to ensure that the user cannot add himself to a
        group where he has no permissions on.
        To allow password changes (or name changes), the change is also permitted if the user does not
        try to change the group (new groups are a subset of the groups the user is a member of)
        """
        groups = data['groups']
        if all(self.context['request'].user.has_perm("change_group", group) for group in groups) or set(groups) <= set(
                self.context['request'].user.groups.all()):
            return data
        else:
            raise PermissionDenied()

    def create(self, validated_data):
        """
        This is used to assign permissions to the newly created user.
        Since this method is only used for users which are created by an admin, 
        the admin group of the corresponding company gets change permissions assigned.
        Change permission is also given to the user himself.
        In addition, global permissions are assigned since they are needed in some special cases.
        Per definition, a accountant (i.e. a user that is created by an admin) cannot create companies.
        For simplification, the ObjectPermissionsAssignmentMixin can be used.
        Minor security "feature" :) : accountants can create other accountants.
        """
        user = super(UserSerializer, self).create(validated_data)
        for i in user.groups.all():
            if i.accountants.exists():
                company = get_object_or_404(
                    models.Company, pk=i.accountants.all().first().id)
                assign_perm("change_user", company.admins, user)
                assign_perm("view_user", company.admins, user)
                assign_perm("delete_user", company.admins, user)
        assign_perm("change_user", user, user)
        assign_perm("view_user", user, user)
        assign_perm("delete_user", user, user)

        user.user_permissions.add(
            Permission.objects.get(name='Can add sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add media'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete media'))
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        This is needed for a correct password change. 
        """
        user = super(UserSerializer, self).update(instance, validated_data)
        if validated_data.get('password') is not None:
            user.set_password(validated_data['password'])
        user.save()
        return user


class RegisterUserSerializer(serializers.ModelSerializer):
    """
    The serializer for the user model.
    This is only used for anonymous users.
    For the serializer representing data to 
    authenticated users, please see the UserSerializer.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        """
        This is used to assign permissions to the newly created user.
        Since this method is only used for users which are created by an admin, 
        the admin group of the corresponding company gets change permissions assigned.
        Change permission is also given to the user himself.
        In addition, global permissions are assigned since they are needed in some special cases.
        This user is able to create companies.
        For simplification, the ObjectPermissionsAssignmentMixin can be used.
        """
        user = super(RegisterUserSerializer, self).create(validated_data)
        assign_perm("change_user", user, user)
        assign_perm("view_user", user, user)
        assign_perm("delete_user", user, user)
        user.set_password(validated_data['password'])
        user.user_permissions.add(
            Permission.objects.get(name='Can add company'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add media'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete company'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete media'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change company'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change media'))

        user.save()
        return user


class GroupSerializer(serializers.ModelSerializer):
    """
    The serializer for the group model.
    """
    companies = serializers.SerializerMethodField(read_only=True)
    companyName = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Group
        fields = "__all__"

    def get_companies(self, obj):
        """
        This is provides helpful information to the frontend.
        It lists all companies the group is a member of.
        """
        groupCompanies = get_objects_for_group(
            obj, "view_company", klass=models.Company)
        return [x.id for x in groupCompanies]

    def get_companyName(self, obj):
        """
        This is provides helpful information to the frontend.
        It lists all companies (names!) the group is a member of.
        Redundant information, but it simplifies the frontend.
        """
        groupCompanies = get_objects_for_group(
            obj, "view_company", klass=models.Company)
        return [x.name for x in groupCompanies]


class MediaSerializer(serializers.ModelSerializer, ObjectPermissionsAssignmentMixin):
    """
    The serializer for the media model.
    """
    class Meta:
        model = models.Media
        fields = "__all__"

    def validate(self, data):
        """
        This ensures that a media (invoice) can only be seen within a company.
        """
        company = data['company']
        if self.context['request'].user.has_perm("view_company", company):
            return data
        else:
            raise PermissionDenied()

    def get_permissions_map(self, created):
        """
        This function is called by the permission assignment mixin.
        The returned permissions are then assigned on the object.
        """
        company = get_object_or_404(models.Company, pk=self.data['company'])
        admins = company.admins
        accountants = company.accountants
        return {
            'view_media': [admins, accountants],
            'change_media': [admins, accountants],
            'delete_media': [admins, accountants]
        }
