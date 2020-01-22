from django.contrib.auth.models import Group, Permission, User
from guardian.shortcuts import (assign_perm, get_groups_with_perms,
                                get_objects_for_group, get_objects_for_user)
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework_guardian.serializers import \
    ObjectPermissionsAssignmentMixin

from . import models


class CompanySerializer(serializers.ModelSerializer, ObjectPermissionsAssignmentMixin):
    groups = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Company
        fields = ['name', 'description', 'groups', 'id']

    def create(self, validated_data):
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
        groupsForCompany = get_groups_with_perms(obj)
        return [x.id for x in groupsForCompany]

    def get_permissions_map(self, created):
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
    gross = serializers.SerializerMethodField()
    invNo = serializers.SerializerMethodField()

    class Meta:
        model = models.Sale
        fields = '__all__'

    def get_gross(self, obj):
        return obj.net * (1+obj.vat)

    def get_invNo(self, obj):
        return str(obj.invDate.year) + str(obj.id)

    def validate(self, data):
        company = data['company']
        if self.context['request'].user.has_perm("view_company", company):
            return data
        else:
            raise PermissionDenied()

    def get_permissions_map(self, created):
        company = get_object_or_404(models.Company, pk=self.data['company'])
        admins = company.admins
        accountants = company.accountants
        return {
            'view_sale': [admins, accountants],
            'change_sale': [admins, accountants],
            'delete_sale': [admins, accountants]
        }


class PurchaseSerializer(serializers.ModelSerializer, ObjectPermissionsAssignmentMixin):
    gross = serializers.SerializerMethodField()

    class Meta:
        model = models.Purchase
        fields = '__all__'

    def get_gross(self, obj):
        return obj.net * (1+obj.vat)

    def validate(self, data):
        company = data['company']
        if self.context['request'].user.has_perm("view_company", company):
            return data
        else:
            raise PermissionDenied()

    def get_permissions_map(self, created):
        company = get_object_or_404(models.Company, pk=self.data['company'])
        admins = company.admins
        accountants = company.accountants
        return {
            'view_purchase': [admins, accountants],
            'change_purchase': [admins, accountants],
            'delete_purchase': [admins, accountants]
        }


class VatReportSerializer(serializers.Serializer):
    company = serializers.IntegerField()
    vatIn = serializers.FloatField()
    vatOut = serializers.FloatField()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    companies = serializers.SerializerMethodField(read_only=True)
    isAdminOf = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password',
                  'first_name', 'last_name', 'groups', 'companies', 'isAdminOf']

    def get_isAdminOf(self, obj):
        userCompanies = get_objects_for_user(
            obj, "change_company", klass=models.Company, accept_global_perms=False)
        return [x.id for x in userCompanies]

    def get_companies(self, obj):
        userCompanies = get_objects_for_user(
            obj, "view_company", klass=models.Company)
        return [x.id for x in userCompanies]

    def validate(self, data):
        groups = data['groups']
        if all(self.context['request'].user.has_perm("change_group", group) for group in groups):
            return data
        else:
            raise PermissionDenied()

    def create(self, validated_data):
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
        user.set_password(validated_data['password'])
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
        user.save()
        return user

    def update(self, instance, validated_data):
        if validated_data.get('password') is not None:
            instance.set_password(validated_data['password'])
        if validated_data.get('email') is not None:
            instance.email = validated_data['email']
        if validated_data.get('username') is not None:
            instance.username = validated_data['username']
        if validated_data.get('first_name') is not None:
            instance.first_name = validated_data['first_name']
        if validated_data.get('last_name') is not None:
            instance.last_name = validated_data['last_name']
        instance.save()
        return instance


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
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
    companies = serializers.SerializerMethodField(read_only=True)
    companyName = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Group
        fields = "__all__"

    def get_companies(self, obj):
        groupCompanies = get_objects_for_group(
            obj, "view_company", klass=models.Company)
        return [x.id for x in groupCompanies]

    def get_companyName(self, obj):
        groupCompanies = get_objects_for_group(
            obj, "view_company", klass=models.Company)
        return [x.name for x in groupCompanies]


class MediaSerializer(serializers.ModelSerializer, ObjectPermissionsAssignmentMixin):
    class Meta:
        model = models.Media
        fields = "__all__"

    def validate(self, data):
        company = data['company']
        if self.context['request'].user.has_perm("view_company", company):
            return data
        else:
            raise PermissionDenied()

    def get_permissions_map(self, created):
        company = get_object_or_404(models.Company, pk=self.data['company'])
        admins = company.admins
        accountants = company.accountants
        return {
            'view_media': [admins, accountants],
            'change_media': [admins, accountants],
            'delete_media': [admins, accountants]
        }
