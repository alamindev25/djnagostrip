from django.shortcuts import render

# Create your views here.
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

from product.models import Product, Order


class ProductListView(View):
    def get(self, request):
        products = Product.objects.all()
        return render(
            request,
            "product/product_list.html",
            {"products": products}
        )


class CheckoutView(LoginRequiredMixin, View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        return render(
            request,
            "product/checkout.html",
            {"product": product}
        )


def success(request):
    return JsonResponse({"status": "Success"})

def cancel(request):
    return JsonResponse({"status": "Cancelled"})


@method_decorator(csrf_exempt, name="dispatch")
class CreatePaymentView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        order = Order.objects.create(
            user=request.user,
            product=product,
            amount=product.price
        )
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, price_1234) of the product you want to sell
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': product.name,
                        },
                        'unit_amount': int(product.price * 100),
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            customer_email=request.user.email,
            success_url="http://localhost:8000/success/",
            cancel_url="http://localhost:8000/cancel/",
        )

        order.stripe_checkout_session_id = checkout_session.id
        order.save()
        return redirect(checkout_session.url)
    
@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request):
        return JsonResponse({"status": "unhandled_event"})
