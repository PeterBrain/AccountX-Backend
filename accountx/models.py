from django.contrib.auth.models import User, Group
from django.db import models


class Company(models.Model):
    name = models.TextField()
    description = models.TextField(null=True)
    accountants = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="accountants")
    admins = models.ForeignKey(Group, on_delete=models.CASCADE,related_name="admins")

    def __str__(self):
        return self.name


class Media(models.Model):
    original_file_name = models.TextField()
    content_type = models.TextField()
    size = models.PositiveIntegerField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE)


class Sale(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    bookingType = models.TextField()
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
    bookingType = models.TextField()
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
