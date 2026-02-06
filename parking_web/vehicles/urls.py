"""URL configuration for vehicles app"""

from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.vehicle_list_view, name='vehicle_list'),
    path('add/', views.add_vehicle_view, name='add_vehicle'),
    path('edit/<int:vehicle_id>/', views.edit_vehicle_view, name='edit_vehicle'),
    path('delete/<int:vehicle_id>/', views.delete_vehicle_view, name='delete_vehicle'),
]
