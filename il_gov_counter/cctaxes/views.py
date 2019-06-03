from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .models import TaxCode, PropAddress
from django.views import generic
from django.utils import timezone
import csv

def index(request):
    prompt = "Please enter an address PIN"
    return HttpResponse(prompt)

def detail(request, pin):
    return HttpResponse("You're looking at the address with the PIN %s." % pin)

def results(request, tax_code):
    response = "Your address is in the tax code: %s."
    return HttpResponse(response % tax_code)

def search(request):
    if request.method == 'POST':
        search_id = request.POST.get('textfield', None)
        try:
            pin_in = PropAddress.objects.get(pin = search_id)
            #do something with user
            html = ("<H1>%s</H1>", pin_in)
            return HttpResponse(html)
        except PropAddress.DoesNotExist:
            return HttpResponse("PIN not found. Please enter a correct PIN")
    else:
        return render(request, 'form.html')
