"""URL configuration for bookings app"""

from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('browse/', views.browse_slots_view, name='browse_slots'),
    path('book/<int:slot_id>/', views.book_slot_view, name='book_slot'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('booking/<int:booking_id>/', views.booking_detail_view, name='booking_detail'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking_view, name='cancel_booking'),
    path('booking/<int:booking_id>/qr/', views.view_qr_view, name='view_qr'),
]
