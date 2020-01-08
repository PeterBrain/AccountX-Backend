from django.contrib.auth.models import Group, Permission, User
from guardian.shortcuts import (assign_perm, get_objects_for_group,
                                get_objects_for_user)
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework_guardian.serializers import \
    ObjectPermissionsAssignmentMixin

from . import models


class CompanySerializer(serializers.ModelSerializer, ObjectPermissionsAssignmentMixin):
    class Meta:
        model = models.Company
        fields = '__all__'

    def get_permissions_map(self, created):
        current_user = self.context['request'].user
        company = self.data['id']
        if(Group.objects.filter(name="company" + str(company)+'_accountants').exists()):
            admins = Group.objects.get(
                name="company" + str(company) + '_admins')
            accountants = Group.objects.get(
                name="company" + str(company)+'_accountants')
        else:
            admins = Group.objects.create(
                name="company" + str(company) + '_admins')
            accountants = Group.objects.create(
                name="company" + str(company)+'_accountants')
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
    def get_gross(self,obj):
        return obj.net * (1+obj.ust)
    def get_invNo(self, obj):
        return str(obj.invDate.year) + str(obj.id) 
    def validate(self, data):
        company = data['company']
        bt = data['bookingType']
        if self.context['request'].user.has_perm("view_company", company) and self.context['request'].user.has_perm("view_bookingtype", bt):
            return data
        else:
            raise PermissionDenied()
    def get_permissions_map(self, created):
        company = self.data['company']
        admins = Group.objects.get(name="company" + str(company) + '_admins')
        accountants = Group.objects.get(
            name="company" + str(company)+'_accountants')
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
    def get_gross(self,obj):
        return obj.net * (1+obj.ust)
    def validate(self, data):
        company = data['company']
        bt = data['bookingType']
        if self.context['request'].user.has_perm("view_company", company) and self.context['request'].user.has_perm("view_bookingtype", bt):
            return data
        else:
            raise PermissionDenied()

    def get_permissions_map(self, created):
        company = self.data['company']
        admins = Group.objects.get(name="company" + str(company) + '_admins')
        accountants = Group.objects.get(
            name="company" + str(company)+'_accountants')
        return {
            'view_purchase': [admins, accountants],
            'change_purchase': [admins, accountants],
            'delete_purchase': [admins, accountants]
        }

class BookingTypeSerializer(serializers.ModelSerializer, ObjectPermissionsAssignmentMixin):
    class Meta:
        model = models.BookingType
        fields = "__all__"

    def validate(self, data):
        company = data['company']
        if self.context['request'].user.has_perm("change_company", company):
            return data
        else:
            raise PermissionDenied()

    def get_permissions_map(self, created):
        company = self.data['company']
        admins = Group.objects.get(name="company" + str(company) + '_admins')
        accountants = Group.objects.get(
            name="company" + str(company)+'_accountants')
        return {
            'view_bookingtype': [admins, accountants],
            'change_bookingtype': [admins],
            'delete_bookingtype': [admins]
        }

class UstReportSerializer(serializers.Serializer):
    company = serializers.IntegerField()
    ustIn = serializers.FloatField()
    ustOut = serializers.FloatField()
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'groups']

    def validate(self, data):
        groups = data['groups']
        if all(self.context['request'].user.has_perm("change_group", group) for group in groups):
            return data
        else:
            raise PermissionDenied()

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.user_permissions.add(
            Permission.objects.get(name='Can add sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete purchase'))
        user.save()
        return user
    def update(self, instance,validated_data):
        if validated_data['password'] is not None:
            instance.set_password(validated_data['password'])
        if validated_data['email'] is not None:
            instance.email = validated_data['email']
        instance.save()
        return instance


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = super(RegisterUserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.user_permissions.add(
            Permission.objects.get(name='Can add company'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add booking type'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete company'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can delete booking type'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change company'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change sale'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change purchase'))
        user.user_permissions.add(
            Permission.objects.get(name='Can change booking type'))

        user.save()
        return user


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Media
        fields = "__all__"
