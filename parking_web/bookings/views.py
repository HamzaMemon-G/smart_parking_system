from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ParkingSlot, Booking
from vehicles.models import Vehicle
import json


def auto_expire_old_bookings():
    """Automatically expire pending bookings past their deadline"""
    with connection.cursor() as cursor:
        # Find expired bookings
        cursor.execute("""
            SELECT b.booking_id, b.ticket_number, b.slot_id
            FROM bookings b
            WHERE b.booking_status = 'pending' 
            AND b.checkin_deadline IS NOT NULL
            AND b.checkin_deadline < %s
        """, [timezone.now()])
        expired = cursor.fetchall()
        
        if expired:
            for booking in expired:
                booking_id, ticket_number, slot_id = booking
                
                # Mark booking as cancelled
                cursor.execute("""
                    UPDATE bookings 
                    SET booking_status = 'cancelled', 
                        notes = 'Auto-cancelled: Check-in deadline expired',
                        forfeited = 1
                    WHERE booking_id = %s
                """, [booking_id])
                
                # Free up the parking slot
                cursor.execute("""
                    UPDATE parking_slots 
                    SET status = 'available'
                    WHERE slot_id = %s
                """, [slot_id])
            
            connection.commit()
            print(f"✓ Auto-expired {len(expired)} booking(s)")


@login_required
def dashboard_view(request):
    """User dashboard with active bookings and quick actions"""
    # Auto-expire old bookings first
    auto_expire_old_bookings()
    # Get active bookings
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT b.booking_id, b.ticket_number, b.slot_id, b.booking_status,
                   b.checkin_deadline, b.checkin_time, b.checkout_time,
                   b.qr_code_path, b.forfeited,
                   ps.slot_number, ps.floor, ps.section
            FROM bookings b
            JOIN parking_slots ps ON b.slot_id = ps.slot_id
            WHERE b.user_id = %s AND b.booking_status IN ('pending', 'active')
            ORDER BY b.booking_time DESC
        """, [request.user.user_id])
        active_bookings = cursor.fetchall()
    
    # Get available slots count
    available_count = ParkingSlot.objects.filter(status='available').count()
    
    context = {
        'active_bookings': active_bookings,
        'available_count': available_count,
    }
    return render(request, 'bookings/dashboard.html', context)


@login_required
def browse_slots_view(request):
    """Browse available parking slots"""
    floor_filter = request.GET.get('floor', '')
    vehicle_type = request.GET.get('vehicle_type', '')
    
    slots = ParkingSlot.objects.filter(status='available')
    
    if floor_filter:
        slots = slots.filter(floor=floor_filter)
    if vehicle_type:
        slots = slots.filter(vehicle_type=vehicle_type)
    
    # Get unique floors for filter
    floors = ParkingSlot.objects.values_list('floor', flat=True).distinct()
    
    context = {
        'slots': slots,
        'floors': floors,
        'selected_floor': floor_filter,
        'selected_vehicle_type': vehicle_type,
    }
    return render(request, 'bookings/browse_slots.html', context)


@login_required
def book_slot_view(request, slot_id):
    """Book a parking slot"""
    slot = get_object_or_404(ParkingSlot, slot_id=slot_id)
    
    if slot.status != 'available':
        messages.error(request, 'This slot is not available')
        return redirect('bookings:browse_slots')
    
    # Get user vehicles
    vehicles = Vehicle.objects.filter(user=request.user)
    
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle_id')
        hours = int(request.POST.get('hours', 1))
        
        if not vehicle_id:
            messages.error(request, 'Please select a vehicle')
            return render(request, 'bookings/book_slot.html', {'slot': slot, 'vehicles': vehicles})
        
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id, user=request.user)
        
        # Calculate cost
        from decimal import Decimal
        cost = Decimal(str(slot.base_price_per_hour)) * Decimal(hours)
        
        # Check wallet balance
        if request.user.wallet_balance < cost:
            messages.error(request, f'Insufficient balance. Required: ₹{cost}, Available: ₹{request.user.wallet_balance}')
            return redirect('accounts:wallet_recharge')
        
        # Generate ticket number (use PKG prefix to match Tkinter app)
        import uuid
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:4].upper()
        ticket_number = f"PKG{timestamp}{unique_id}"
        
        # Calculate deadlines
        checkin_deadline = timezone.now() + timedelta(minutes=settings.BOOKING_CHECKIN_WINDOW_MINUTES)
        booking_time = timezone.now()
        
        # Create booking using raw SQL
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO bookings (
                        user_id, vehicle_id, slot_id, ticket_number, booking_status,
                        total_amount, base_amount, checkin_deadline, duration_hours,
                        booking_time, entry_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    request.user.user_id, vehicle.vehicle_id, slot.slot_id,
                    ticket_number, 'pending', cost, cost, checkin_deadline, hours,
                    booking_time, booking_time
                ])
                booking_id = cursor.lastrowid
                connection.commit()
                print(f"✓ Booking created: ID={booking_id}, Ticket={ticket_number}")
        except Exception as e:
            print(f"✗ Error creating booking: {e}")
            messages.error(request, f'Failed to create booking: {str(e)}')
            return redirect('bookings:browse_slots')
        
        # Get the booking object to generate QR - refresh from database
        booking = Booking.objects.get(booking_id=booking_id)
        booking.refresh_from_db()  # Ensure we have fresh data
        
        # Debug: Verify ticket number matches
        print(f"DEBUG: Created booking {booking_id} with ticket {ticket_number}")
        print(f"DEBUG: Booking object has ticket {booking.ticket_number}")
        
        booking.generate_qr_data()
        
        # Update slot status
        slot.status = 'reserved'
        slot.save()
        
        # Deduct from wallet
        request.user.wallet_balance -= cost
        request.user.save()
        
        # Record payment
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO payments (booking_id, amount, payment_method, transaction_id, payment_time)
                VALUES (%s, %s, %s, %s, %s)
            """, [booking_id, cost, 'wallet', f'WLT{booking_id}', timezone.now()])
            connection.commit()
        
        messages.success(request, f'Booking successful! Ticket: {ticket_number}. Check in within 30 minutes.')
        return redirect('bookings:view_qr', booking_id=booking_id)
    
    context = {
        'slot': slot,
        'vehicles': vehicles,
    }
    return render(request, 'bookings/book_slot.html', context)


@login_required
def my_bookings_view(request):
    """View all user bookings"""
    # Auto-expire old bookings first
    auto_expire_old_bookings()
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT b.booking_id, b.ticket_number, b.booking_status, b.total_amount,
                   b.booking_time, b.checkin_time, b.checkout_time, b.forfeited,
                   ps.slot_number, ps.floor, ps.section,
                   v.vehicle_number
            FROM bookings b
            JOIN parking_slots ps ON b.slot_id = ps.slot_id
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            WHERE b.user_id = %s
            ORDER BY b.booking_time DESC
        """, [request.user.user_id])
        bookings = cursor.fetchall()
    
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def booking_detail_view(request, booking_id):
    """View booking details"""
    # Auto-expire old bookings first
    auto_expire_old_bookings()
    
    booking = get_object_or_404(Booking, booking_id=booking_id, user_id=request.user.user_id)
    
    return render(request, 'bookings/booking_detail.html', {'booking': booking})


@login_required
def cancel_booking_view(request, booking_id):
    """Cancel a pending booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user_id=request.user.user_id)
    
    if booking.booking_status != 'pending':
        messages.error(request, 'Only pending bookings can be cancelled')
        return redirect('bookings:my_bookings')
    
    # Check if not expired
    if booking.is_expired():
        messages.error(request, 'Booking already expired')
        return redirect('bookings:my_bookings')
    
    # Cancel booking
    booking.booking_status = 'cancelled'
    booking.save()
    
    # Free slot
    slot = booking.slot
    slot.status = 'available'
    slot.save()
    
    # Refund to wallet (deduct 10% cancellation fee)
    from decimal import Decimal
    refund_amount = booking.total_amount * Decimal('0.9')
    request.user.wallet_balance += refund_amount
    request.user.save()
    
    messages.success(request, f'Booking cancelled. ₹{refund_amount} refunded to wallet (10% cancellation fee)')
    return redirect('bookings:my_bookings')


@login_required
def view_qr_view(request, booking_id):
    """View QR code for booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user_id=request.user.user_id)
    
    if not booking.qr_code_path:
        booking.generate_qr_data()
    
    # Check if expired
    expired = booking.is_expired() if booking.booking_status == 'pending' else False
    
    # Calculate time remaining
    time_remaining = None
    if booking.booking_status == 'pending' and not expired:
        time_remaining = (booking.checkin_deadline - timezone.now()).total_seconds() / 60
    
    context = {
        'booking': booking,
        'expired': expired,
        'time_remaining': int(time_remaining) if time_remaining else None,
    }
    return render(request, 'bookings/view_qr.html', context)
