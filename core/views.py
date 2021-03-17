from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.views import View
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json

from .models import Item, OrderItem, Order, BillingAddress, Payment, Coupon
from .forms import CheckoutForm

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(ListView):
    model = Item
    template_name = 'home.html'

    paginate_by = 10


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'account/order_summary.html', context=context) 
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active user")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


class CheckOutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        context = {
            'form': form
        }
        return render(self.request, "checkout.html", context=context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid(): 
                address_line_1 = form.cleaned_data.get('address_line_1')
                address_line_2 = form.cleaned_data.get('address_line_2')
                country = form.cleaned_data.get('country')
                zip_code = form.cleaned_data.get('zip_code')
                # TODO: add functionality for these fields
                # same_shipping_address = form.cleaned_data.get('same_shipping_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user=self.request.user,
                    address_line_1=address_line_1,
                    address_line_2=address_line_2,
                    country=country,
                    zip_code=zip_code
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                # TODO: add a redirect to selected payment option
                if payment_option == 'S':
                    return redirect("core:payment", payment_option="stripe")
                elif payment_option == 'P':
                    return redirect("core:payment", payment_option="paypal")
                else:
                    messages.warning(self.request, "Invalid paymemnt option selected")
                    return redirect("core:checkout")
            
            messages.warning(self.request, "Failed to checkout ")
            return redirect("core:checkout")     
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active user")
            return redirect("core:order_summary")   


class PaymentLandingView(TemplateView):
    template_name = 'payment.html'

    def get_context_data(self, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False) 
        context =  super(PaymentLandingView, self).get_context_data(**kwargs)
        context.update({
            "order": order,
            "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY
        })
        return context


class PaymentView(View): 
    def post(self, request, *args, **kwargs): 
        try: 
            order = Order.objects.get(user=self.request.user, ordered=False ) 
            amount = int(order.get_total() * 100) 
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
            )
            # create payment
            payment = Payment()
            payment.stripe_charge_id = intent.id
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # update order items
            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            # assign payment to order
            # order.payment = payment
            # order.ordered = True
            # order.save()

            return JsonResponse({
                "clientSecret": intent['client_secret']
            }) 

        except Exception as e: 
            return JsonResponse({ "error" :str(e) })



@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user, 
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    
    if order_qs.exists():
        order = order_qs[0]
        # check if the item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Item quantity was updated")
            return redirect('core:order_summary') 
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart")
            return redirect('core:order_summary')
    
    else:
        order_date = timezone.now()
        order = Order.objects.create(user=request.user, order_date=order_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart")
        return redirect("core:order_summary" )


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            # item exists in order - DELETE IT
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order_item.quantity = 1
            order_item.save()
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart")
            return redirect('core:order_summary')

        else:
            messages.info(request, "This item was not in your cart")
            return redirect('core:product', slug=slug)

    else:
        # order does not exist
        messages.info(request, "You do not have an active order")
        return redirect('core:product', slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            # item exists in order - DELETE IT
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]

            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                remove_from_cart(request, slug)

            messages.info(request, "Item quantity was updated")
            return redirect('core:order_summary')

        else:
            messages.info(request, "This item was not in your cart")
            return redirect('core:product', slug=slug)

    else:
        # order does not exist
        messages.info(request, "You do not have an active order")
        return redirect('core:product', slug=slug) 

def get_coupon(code):

def add_coupon(request, code):
    try:
        order_qs = Order.objects.get(user=request.user, ordered=False)

        coupon = Coupon.objects.get(code=code)

    except ObjectDoesNotExist:
        messages.info(request, "You do not have an active order")
        return redirect("core:checkout")