# -*- coding: utf-8 -*-
from django import forms
# fill in custom user info then save it
from .models import *
from django.forms import ModelForm, Textarea, TextInput, HiddenInput, CheckboxInput, RadioSelect

CHOICES = (('B', 'Buy',), ('S', 'Sell',))


class ManageTransaction(ModelForm):

    type = forms.ChoiceField(
        required=False,
        widget=forms.RadioSelect,
        choices=CHOICES,
        label="Type")

    currency_from = forms.ModelChoiceField(
        required=False,
        queryset=Currency.objects.all(),
        label="Currency From")

    class Meta:
        model = Transaction
        fields = '__all__'
        exclude = ['deleted', 'disabled',
                   'kraken_price', 'rate',
                                   'profit', 'bulk_loaded',
                                   'rate', 'created_on']


class DateSearchForm(forms.Form):
    date = forms.DateField(required=False, label="Search by Date")


class FilterSearchForm(forms.Form):
    date = forms.DateField(required=False, label="by Date")
    currency = forms.ModelChoiceField(
        required=False,
        queryset=Currency.objects.all(),
        label="by Currency")
    resource = forms.ModelChoiceField(
        required=False,
        queryset=Resource.objects.all(),
        label="by Resource")


class ManageBulkloadTransaction(forms.Form):
    csvfile = forms.FileField(label="Upload a file")
    delimiter = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'size': '1'}),
        label="Record Delimiter",
        initial=",")
    first_head = forms.BooleanField(
        label="First line is header ",
        required=False,
        initial=True)


class ResourcePickForm(forms.Form):
    currency_from = forms.ModelChoiceField(
        required=True,
        queryset=Currency.objects.all(),
        label="Select From Currency")
    resource = forms.ModelChoiceField(
        required=True,
        queryset=Resource.objects.all(),
        label="Select Resource")


class BalanceForm(forms.Form):

    class Meta:
        model = Balance
        fields = '__all__'
