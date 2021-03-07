from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'Paypal')
)


class CheckoutForm(forms.Form):
    address_line_1 = forms.CharField(widget=forms.TextInput(attrs={
        "class":"form-control", 
        "placeholder":"1234 Main St"
    }
    ))
    address_line_2 = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "class":"form-control", 
        "placeholder":"Area/Locality"
    }
    ))

    country = CountryField(blank_label='(select country)').formfield(
        widget=CountrySelectWidget(attrs={
            'class': "custom-select d-block w-100"
        }))
    
    zip_code = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control",
    }))
    
    same_billing_address = forms.BooleanField(required=False)
    save_info = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES)
