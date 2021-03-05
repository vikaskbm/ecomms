from django.shortcuts import render
from .models import Item
from django.views.generic import ListView, DetailView


class HomeView(ListView):
    model = Item
    template_name = 'home.html'


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


def checkout(request):
    return render(request, "checkout.html")