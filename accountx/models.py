from django.contrib.auth.models import User
from django.db import models


class Company(models.Model):
    name = models.TextField()
    description = models.TextField(null=True)

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
    company = models.ForeignKey(Company, on_delete=models.CASCADE)


class Sale(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    bookingType = models.ForeignKey(BookingType, on_delete=models.CASCADE)
    invDate = models.DateField()
    customer = models.TextField()
    project = models.TextField()
    vat = models.FloatField()
    net = models.FloatField()
    notes = models.TextField(blank=True)
    cashflowdate = models.DateField(null=True)
    invoice = models.ManyToManyField('Media', blank=True)

    def __str__(self):
        return str(self.invDate.year) + str(self.pk)


class Purchase(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    bookingType = models.ForeignKey(BookingType, on_delete=models.CASCADE)
    invNo = models.TextField()
    invDate = models.DateField()
    biller = models.TextField()
    vat = models.FloatField()
    net = models.FloatField()
    cashflowdate = models.DateField(null=True)
    notes = models.TextField(blank=True)
    invoice = models.ManyToManyField('Media', blank=True)

    def __str__(self):
        return self.invNo
