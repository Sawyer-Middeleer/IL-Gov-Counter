from django.db import models
from django import forms
from django.conf import settings
from django.utils import timezone
from bs4 import BeautifulSoup
import urllib
import re
import csv
import io

# user input
class PropAddress(models.Model):
    pin = models.CharField(max_length=14)
    tax_code = models.CharField(max_length=6)
    value = models.CharField(max_length=10)
    # tax_code needs to come from scraping the assessor's website
    def __str__(self):
        return self.pin

    def get_absolute_url(self):
        """Returns the url to access a particular instance of the model."""
        return reverse('model-detail-view', args=[str(self.id)])

    def get_tax_code(self):
        """Scrapes the Cook County Assessor's website to grab the PIN's tax code"""
        with urllib.request.urlopen('https://www.cookcountyassessor.com/pin/'+self.pin) as url:
            html = url.read()
        bsObj = BeautifulSoup(html)
        tax_code_obj = bsObj.find_all("span", {"class":"detail-row--detail large"})[3]
        self.tax_code = tax_code_obj.get_text()
        value_obj = bsObj.find_all("span", {"class":"detail-row--detail"})[12]
        self.value = value_obj.get_text()
        self.save()

# from tax_rates csv
class TaxCode(models.Model):
    tax_year = models.IntegerField(default=2017)
    tax_code = models.IntegerField(default=12345)
    agency = models.IntegerField(default=10010000)
    agency_name = models.CharField(default="COUNTY OF COOK", max_length=50)
    agency_rate = models.DecimalField(default=0, decimal_places=3, max_digits=6)
    tax_code_rate = models.DecimalField(default=0, decimal_places=3, max_digits=6)
    assessment_district = models.CharField(default="Barrington", max_length=50)
    taxing_body_count = models.IntegerField(default=0)
    assessment_ratio = models.DecimalField(default=0, decimal_places=3, max_digits=6)
    equalization_factor = models.DecimalField(default=2.0, decimal_places=3, max_digits=6)
    effective_property_tax_rate = models.DecimalField(default=0, decimal_places=3, max_digits=6)
    tax_rate_proportion = models.DecimalField(default=0, decimal_places=3, max_digits=6)
    etr_share = models.DecimalField(default=0, decimal_places=3, max_digits=6)
    agency_type = models.CharField(default="County", max_length=50)
    category_etr = models.DecimalField(default=0, decimal_places=3, max_digits=6)
    user_address = models.ForeignKey(PropAddress, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.tax_code)

    def get_absolute_url(self):
        """Returns the url to access a particular instance of the model."""
        return reverse('model-detail-view', args=[str(self.id)])

    def read_tax_rates_data(self):
        with open(r'C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\il_gov_counter\cctaxes\static\cctaxes\tax_rates_full.csv', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0] != 'Tax Year':
                    _, created = TaxCode.objects.get_or_create(
                        tax_year=row[0],
                        tax_code=row[1],
                        agency=row[2],
                        agency_name=row[3],
                        agency_rate=row[4],
                        tax_code_rate=row[5],
                        assessment_district=row[6],
                        taxing_body_count=row[7],
                        assessment_ratio=row[8],
                        equalization_factor=row[9],
                        effective_property_tax_rate=row[10],
                        tax_rate_proportion=row[11],
                        etr_share=row[12],
                        agency_type=row[13],
                        category_etr=row[14]
                    )
                # creates a tuple of the new object or
                # current object and a boolean of if it was created
