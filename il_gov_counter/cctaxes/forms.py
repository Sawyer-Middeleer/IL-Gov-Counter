from django import forms
from django.forms import ModelForm
from .models import TaxCode, PropAddress


class PinForm(forms.ModelForm):
#     def clean_pin(self):
#       data = self.cleaned_data['due_back']
#
#       if data < datetime.date.today():
#           raise ValidationError(_('Invalid date - renewal in past'))
#
#       if data > datetime.date.today() + datetime.timedelta(weeks=4):
#           raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))
#
#       # Remember to always return the cleaned data.
#       return data

    class Meta:
        model = PropAddress
        fields = ['pin']
