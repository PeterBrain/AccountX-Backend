from rest_framework import serializers
from . import models
from django.contrib.auth.models import User
from rest_framework.exceptions import PermissionDenied


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
        if self.context['request'].user in company.accountants.all() or self.context['request'].user in company.admins.all():
            return data
        else:
            raise PermissionDenied()


class BookingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookingType
        fields = "__all__"

    def validate(self, data):
        company = data['company']
        if self.context['request'].user.id in company.admins.all():
            return data
        else:
            raise PermissionDenied()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Media
        fields = "__all__"
