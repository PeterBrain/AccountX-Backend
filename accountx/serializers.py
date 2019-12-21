from django.contrib.auth.models import Permission, User
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from . import models


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Company
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Booking
        fields = '__all__'

    def validate(self, data):
        company = data['company']
        bt = data['bookingType']
        if self.context['request'].user.has_perm("change_company", company) and self.context['request'].user.has_perm("view_bookingtype", bt):
            return data
        else:
            raise PermissionDenied()


class BookingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookingType
        fields = "__all__"

    def validate(self, data):
        company = data['company']
        if self.context['request'].user.has_perm("change_company", company):
            return data
        else:
            raise PermissionDenied()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'groups']

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.user_permissions.add(
            Permission.objects.get(name='Can add booking'))
        user.save()
        return user

    def validate(self, data):
        groups = data['groups']
        if self.context['request'].user.has_perm("change_group", groups[0]):
            return data
        else:
            raise PermissionDenied()


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
            Permission.objects.get(name='Can add booking'))
        user.user_permissions.add(
            Permission.objects.get(name='Can add booking type'))
        user.save()
        return user


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Media
        fields = "__all__"
