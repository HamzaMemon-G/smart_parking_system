from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from .models import Vehicle


@login_required
def vehicle_list_view(request):
    """List all user vehicles"""
    vehicles = Vehicle.objects.filter(user=request.user)
    return render(request, 'vehicles/vehicle_list.html', {'vehicles': vehicles})


@login_required
def add_vehicle_view(request):
    """Add new vehicle"""
    if request.method == 'POST':
        vehicle_number = request.POST.get('vehicle_number').upper()
        vehicle_type = request.POST.get('vehicle_type')
        brand = request.POST.get('brand')
        model = request.POST.get('model')
        color = request.POST.get('color')
        
        # Check if vehicle already exists
        if Vehicle.objects.filter(vehicle_number=vehicle_number).exists():
            messages.error(request, 'Vehicle with this number already registered')
            return render(request, 'vehicles/vehicle_form.html')
        
        # Create vehicle using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO vehicles (user_id, vehicle_number, vehicle_type, brand, model, color)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [request.user.user_id, vehicle_number, vehicle_type, brand, model, color])
            connection.commit()
        
        messages.success(request, 'Vehicle added successfully')
        return redirect('vehicles:vehicle_list')
    
    return render(request, 'vehicles/vehicle_form.html', {'action': 'Add'})


@login_required
def edit_vehicle_view(request, vehicle_id):
    """Edit existing vehicle"""
    vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id, user=request.user)
    
    if request.method == 'POST':
        vehicle.brand = request.POST.get('brand')
        vehicle.model = request.POST.get('model')
        vehicle.color = request.POST.get('color')
        vehicle.vehicle_type = request.POST.get('vehicle_type')
        vehicle.save()
        
        messages.success(request, 'Vehicle updated successfully')
        return redirect('vehicles:vehicle_list')
    
    return render(request, 'vehicles/vehicle_form.html', {'action': 'Edit', 'vehicle': vehicle})


@login_required
def delete_vehicle_view(request, vehicle_id):
    """Delete vehicle"""
    vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id, user=request.user)
    
    # Check if vehicle has active bookings
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE vehicle_id = %s AND booking_status IN ('pending', 'active')
        """, [vehicle_id])
        active_count = cursor.fetchone()[0]
    
    if active_count > 0:
        messages.error(request, 'Cannot delete vehicle with active bookings')
        return redirect('vehicles:vehicle_list')
    
    vehicle.delete()
    messages.success(request, 'Vehicle deleted successfully')
    return redirect('vehicles:vehicle_list')
