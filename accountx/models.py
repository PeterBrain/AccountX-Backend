from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Company (models.Model):
    name = models.TextField()
    description = models.TextField(null=True)
    accountants = models.ManyToManyField(User, related_name="accountants")
    admins = models.ManyToManyField(User, related_name="admins")

    def __str__(self):
        return self.name


class BookingType(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.TextField()

    def __str__(self):
        return self.name


class Media(models.Model):
    original_file_name = models.TextField()
    content_type = models.TextField()
    size = models.PositiveIntegerField()


class Booking(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    bookingType = models.ForeignKey(BookingType, on_delete=models.CASCADE)
    isNegative = models.BooleanField()
    name = models.TextField()
    invoice = models.ManyToManyField('Media', blank=True)

    def __str__(self):
        return self.name
