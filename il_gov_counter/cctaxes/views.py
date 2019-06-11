from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from .models import TaxCode, PropAddress
from .forms import PinForm
from django.views import generic
from django.utils import timezone
import re
import csv
import string
import numpy as np
import pandas as pd
from django_pandas.io import read_frame
from django.db.models import Avg, Min, Max

def index(request): # home page

    template = loader.get_template('cctaxes/index.html')

    if request.method == 'POST':
        form = PinForm(request.POST)
        if form.is_valid():
            pin_search = form.save()
            return redirect('results', id=pin_search.id)
    else:
        form = PinForm()

    context = {'form': form}
    return render(request,'cctaxes/index.html', context)


def results(request, id):
    property_address = PropAddress.objects.get(id=id)
    property_address.get_tax_code()

    all_codes = TaxCode.objects.filter(tax_year=2017).distinct().order_by('tax_code')
    all_codes_14 = TaxCode.objects.filter(tax_year=2014).distinct()

    prop_tax_code = TaxCode.objects.filter(tax_code=property_address.tax_code).distinct().order_by('-etr_share')
    prop_tax_code_17 = prop_tax_code.filter(tax_year=2017)
    prop_tax_code_14 = prop_tax_code.filter(tax_year=2014)
    prop_tax_17_df = read_frame(prop_tax_code_17)
    by_category = prop_tax_17_df.groupby('agency_type')['tax_rate_proportion'].sum()


    bodies_info = []
    etr_info = []
    tax_table = []

    categories = []
    category_etrs = []
    category_table = []

    for c in prop_tax_code_17:
        bodies_info.append(c.agency_name)
        etr_info.append(float(c.tax_rate_proportion))

    for i in range(prop_tax_code_17[0].taxing_body_count):
        tax_table.append([bodies_info[i], etr_info[i]])

    for row in range(len(by_category)):
        categories.append(by_category.index[row])
        category_etrs.append(float(by_category[row]))
    for i in range(len(categories)):
        category_table.append([categories[i], category_etrs[i]])

    if request.method == 'POST':
        form = PinForm(request.POST)
        if form.is_valid():
            pin_search = form.save()
            return redirect('results', id=pin_search.id)
    else:
        form = PinForm()


    codes = set([])

    for code in all_codes:
        codes.add(code.tax_code)

    etr = round(prop_tax_code_17[0].effective_property_tax_rate, 1)
    etr_14 = round(prop_tax_code_14[0].effective_property_tax_rate, 1)

    home_value = re.sub('[^0-9]','', property_address.value)
    payment = float(etr)/100*float(home_value)*.5

    district_etr_summary = TaxCode.objects.filter(tax_year=2017, assessment_district=prop_tax_code[0].assessment_district).aggregate(Avg('effective_property_tax_rate'), Max('effective_property_tax_rate'), Min('effective_property_tax_rate'))

    cook_county_avg_etr = all_codes.aggregate(Avg('effective_property_tax_rate'))['effective_property_tax_rate__avg']
    cook_county_avg_etr_14 = all_codes_14.aggregate(Avg('effective_property_tax_rate'))['effective_property_tax_rate__avg']

    tax_code_change = (prop_tax_code_17[0].tax_code_rate - prop_tax_code_14[0].tax_code_rate) / prop_tax_code_14[0].tax_code_rate * 100
    county_change = (cook_county_avg_etr - cook_county_avg_etr_14) / cook_county_avg_etr_14 * 100



    context = {
               'prop_id':property_address.id,
               'prop_val':home_value,
               'prop_tax_code':property_address.tax_code,
               'tax_code_rate':round(prop_tax_code_17[0].tax_code_rate,1),
               'body_count':prop_tax_code_17[0].taxing_body_count,
               'effective_property_tax_rate':etr,
               'effective_property_tax_rate_14':etr_14,
               'payment':round(int(payment),-2),
               'township':prop_tax_code_17[0].assessment_district,
               'tax_data_table':tax_table,
               'category_data_table':category_table,
               'township_etr':round(district_etr_summary['effective_property_tax_rate__avg'], 1),
               'township_min':round(district_etr_summary['effective_property_tax_rate__min'], 1),
               'township_max':round(district_etr_summary['effective_property_tax_rate__max'], 1),
               'categories':categories,
               'category_etrs':category_etrs,
               'tax_codes':codes,
               'by_category':by_category,
               'cook_county_avg_etr':round(cook_county_avg_etr,1),
               'cook_county_avg_etr_14':round(cook_county_avg_etr_14,1),
               'greater_township':prop_tax_code_17[0].effective_property_tax_rate > district_etr_summary['effective_property_tax_rate__avg'],
               'lesser_township':prop_tax_code_17[0].effective_property_tax_rate < district_etr_summary['effective_property_tax_rate__avg'],
               'greater_county':prop_tax_code_17[0].effective_property_tax_rate > all_codes.aggregate(Avg('effective_property_tax_rate'))['effective_property_tax_rate__avg'],
               'lesser_county':prop_tax_code_17[0].effective_property_tax_rate < all_codes.aggregate(Avg('effective_property_tax_rate'))['effective_property_tax_rate__avg'],
               'tax_code_change':round(tax_code_change,1),
               'county_change':round(county_change,1),

               'form':form,
               }

    return render(request, 'cctaxes/results.html', context)


def tax_impact(request):
    property_address = request.session.get('property_address')
    prop_tax_code = request.session.get('prop_tax_code')
    prop_tax_code_17 = request.session.get('prop_tax_code_17')


    context = {
               'property_address':property_address,
    }

    return render(request, 'cctaxes/tax-impact.html', context)
