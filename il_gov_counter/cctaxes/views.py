from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from .models import TaxCode, PropAddress
from .forms import PinForm
from django.views import generic
from django.utils import timezone
import csv

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

    prop_tax_code = TaxCode.objects.filter(tax_code=property_address.tax_code).order_by('-etr_share')
    prop_tax_code_17 = prop_tax_code.filter(tax_year=2017)
    effective_property_tax_rate = prop_tax_code_17[0].effective_property_tax_rate
    body_count = prop_tax_code_17[0].taxing_body_count

    etr_info = []
    bodies_info = []
    for c in prop_tax_code_17:
        bodies_info.append(c.agency_name)
        etr_info.append(c.etr_share)

    if request.method == 'POST':
        form = PinForm(request.POST)
        if form.is_valid():
            pin_search = form.save()
            return redirect('results', id=pin_search.id)
    else:
        form = PinForm()

    context = {
               'prop_id':property_address.id,
               'prop_tax_code':property_address.tax_code,
               'body_count':body_count,
               'effective_property_tax_rate': effective_property_tax_rate,
               'bodies_info':bodies_info,
               'etr_info':etr_info,
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
