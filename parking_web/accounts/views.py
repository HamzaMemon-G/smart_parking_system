from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import connection
from .models import User


def register_view(request):
    """User registration"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'accounts/register.html')
        
        # Create user using raw SQL to maintain compatibility
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, user_type, wallet_balance, loyalty_points)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [name, email, phone, make_password(password), 'customer', 0.0, 0])
        
        messages.success(request, 'Registration successful! Please login.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/register.html')


def login_view(request):
    """User login"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.name}!')
            return redirect('bookings:dashboard')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('home')


@login_required
def profile_view(request):
    """View and edit user profile"""
    if request.method == 'POST':
        user = request.user
        user.name = request.POST.get('name')
        user.phone = request.POST.get('phone')
        
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        user.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html')


@login_required
def wallet_view(request):
    """View wallet balance and transactions"""
    # Get payment history
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.payment_id, p.amount, p.payment_method, p.payment_time, 
                   b.ticket_number, b.slot_id
            FROM payments p
            LEFT JOIN bookings b ON p.booking_id = b.booking_id
            WHERE b.user_id = %s
            ORDER BY p.payment_time DESC
            LIMIT 20
        """, [request.user.user_id])
        transactions = cursor.fetchall()
    
    return render(request, 'accounts/wallet.html', {'transactions': transactions})


@login_required
def wallet_recharge_view(request):
    """Recharge wallet with Razorpay"""
    from decimal import Decimal
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        
        if amount < 10:
            messages.error(request, 'Minimum recharge amount is ₹10')
            return redirect('accounts:wallet_recharge')
        
        # TODO: Integrate Razorpay payment gateway
        # For now, just add to wallet (admin manual approval)
        user = request.user
        user.wallet_balance += amount
        user.save()
        
        messages.success(request, f'₹{amount} added to wallet successfully')
        return redirect('accounts:wallet')
    
    return render(request, 'accounts/wallet_recharge.html')
