from django.db import models
from django import forms

# from tax_rates csv
class TaxCode(models.Model):
    tax_code = models.IntegerField(default=12345)
    tax_year = models.IntegerField(default=2017)
    agency = models.IntegerField(default=10010000)
    agency_name = models.CharField(default="COUNTY OF COOK", max_length=50)
    agency_rate = models.IntegerField(default=0)
    tax_code_rate = models.IntegerField(default=0)
    assessment_district = models.CharField(default="Barrington", max_length=50)
    taxing_body_count = models.IntegerField(default=0)
    slug = models.SlugField(max_length=5)
    def __str__(self):
        return self.tax_code

class AssessmentRatio(models.Model):
    tax_year = models.IntegerField(default=2017)
    assessment_district = models.CharField(default="Barrington", max_length=50)
    assessment_ratio = models.IntegerField(default=0)
    equalization_factor = models.IntegerField(default=2.0)
    def __str__(self):
        return self.assessment_district

# from beautifulsoup scrape
class PropAddress(models.Model):
    pin = models.IntegerField(default=33074170350000)
    tax_code = models.ForeignKey(TaxCode, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=14)
    def __str__(self):
        return self.pin
