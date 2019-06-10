from django import forms
from django.forms import ModelForm
from .models import TaxCode, PropAddress


class PinForm(forms.ModelForm):
    class Meta:
        model = PropAddress
        fields = ['pin']

class HomeValueForm(forms.ModelForm):
    class Meta:
        model = PropAddress
        fields = ['value']
