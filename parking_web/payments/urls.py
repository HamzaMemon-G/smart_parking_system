"""URL configuration for payments app"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create-order/', views.create_razorpay_order_view, name='create_order'),
    path('verify/', views.verify_payment_view, name='verify_payment'),
    path('history/', views.payment_history_view, name='payment_history'),
]
