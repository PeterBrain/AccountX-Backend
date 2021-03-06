# Generated by Django 2.2.8 on 2020-01-22 17:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(unique=True)),
                ('description', models.TextField(null=True)),
                ('accountants', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accountants', to='auth.Group')),
                ('admins', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admins', to='auth.Group')),
            ],
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_file_name', models.TextField()),
                ('content_type', models.TextField()),
                ('size', models.PositiveIntegerField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accountx.Company')),
            ],
        ),
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bookingType', models.TextField()),
                ('invDate', models.DateField()),
                ('customer', models.TextField()),
                ('project', models.TextField()),
                ('vat', models.FloatField()),
                ('net', models.FloatField()),
                ('notes', models.TextField(blank=True, null=True)),
                ('cashflowdate', models.DateField(null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accountx.Company')),
                ('invoice', models.ManyToManyField(blank=True, to='accountx.Media')),
            ],
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bookingType', models.TextField()),
                ('invNo', models.TextField()),
                ('invDate', models.DateField()),
                ('biller', models.TextField()),
                ('vat', models.FloatField()),
                ('net', models.FloatField()),
                ('cashflowdate', models.DateField(null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accountx.Company')),
                ('invoice', models.ManyToManyField(blank=True, to='accountx.Media')),
            ],
        ),
    ]
