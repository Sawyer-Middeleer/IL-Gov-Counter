# Generated by Django 2.2.1 on 2019-06-10 00:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cctaxes', '0003_auto_20190605_2335'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxcode',
            name='assessment_ratio',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=6),
        ),
        migrations.AddField(
            model_name='taxcode',
            name='effective_property_tax_rate',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=6),
        ),
        migrations.AddField(
            model_name='taxcode',
            name='etr_share',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=6),
        ),
        migrations.AddField(
            model_name='taxcode',
            name='tax_rate_proportion',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=6),
        ),
    ]
