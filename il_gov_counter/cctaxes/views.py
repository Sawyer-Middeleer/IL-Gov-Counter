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
    greeting = "Please enter your 14-digit address PIN"
    template = loader.get_template('cctaxes/index.html')

    if request.method == 'POST':
        form = PinForm(request.POST)
        if form.is_valid():
            pin_search = form.save()
            return redirect('results', id=pin_search.id)
    else:
        form = PinForm()

    context = {'greeting': greeting,
               'form': form}
    return render(request,'base.html', context)


def results(request, id):
    greeting = "Search another 14-digit address PIN"
    property_address = PropAddress.objects.get(id=id)
    property_address.get_tax_code()

    prop_tax_code = TaxCode.objects.filter(tax_code=property_address.tax_code).order_by('-agency_rate')
    prop_tax_code_17 = prop_tax_code.filter(tax_year=2017)
    bodies = []
    for c in prop_tax_code_17:
        bodies.append(c.agency_name)
    body_count = len(bodies)

    # taxing_bodies = []
    # for row in tax_codes.iterator():
    #     if row.tax_code == prop_code:
    #         taxing_bodies.append(row.tax_code)

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
               'bodies':bodies,
               'form':form,
               'greeting': greeting,
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
