from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import get_object_or_404, render
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
            pass  # does nothing, just trigger the validation
    else:
        form = PinForm()

    context = {'greeting': greeting,
               'form': form}
    return render(request,'cctaxes/index.html', context)

def results(request):
    pin = PropAddress.pin
    html = urlopen('http://www.cookcountyassessor.com/Property.aspx?mode=details&pin='+pin)
    bsObj = BeautifulSoup(html.read())
    tax_code_obj = bsObj.find(id="ctl00_phArticle_ctlPropertyDetails_lblPropInfoTaxcode")
    tax_code = tax_code_obj.get_text()

    return HttpResponse(response % tax_code)


def get_pin(request):
    # if this is a POST request we need to process the form data
    codes = get_object_or_404(TaxCode, pk=pk)
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PinForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            p = form.save(commit=False)
            p.save()
            # redirect to a new URL:
            return HttpResponseRedirect('cctaxes/results/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PinForm()

    return render(request, 'index.html', {'form':form, 'codes':codes})
