# movies/views.py
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Movie, Profile, Showtime, Seat, Booking, BookingSeat, Screen
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .forms import LoginForm, RegisterForm
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Showtime, Booking, Seat
import string
from razorpay import Utility
import razorpay
from django.conf import settings


def index(request):
    movies = Movie.objects.filter(is_active=True).order_by("title")
    return render(request, "movies/index.html", {"movies": movies})

def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    showtimes = movie.showtimes.filter(start_time__gte=timezone.now()).order_by("start_time")
    return render(request, "movies/movie_detail.html", {"movie": movie, "showtimes": showtimes})

@login_required
def booking_view(request, showtime_id):
    showtime = get_object_or_404(Showtime, id=showtime_id)
    screen = showtime.screen
    seats = Seat.objects.filter(screen=screen).order_by("row_number", "seat_number")
    booked_seat_ids = set(
        BookingSeat.objects.filter(showtime=showtime).values_list("seat_id", flat=True)
    )

    if request.method == "POST":
        selected = request.POST.getlist("seats")

        if not selected:
            messages.error(request, "Please select at least one seat")
            return redirect(request.path)

        with transaction.atomic():
            already_booked = BookingSeat.objects.select_for_update().filter(
                showtime=showtime, seat_id__in=selected
            ).exists()

            if already_booked:
                messages.error(request, "One or more seats were just booked by someone else.")
                return redirect(request.path)

            total_price = showtime.price * len(selected)

            booking = Booking.objects.create(
                user=request.user,
                showtime=showtime,
                total_price=total_price,
                status="pending"
            )

            BookingSeat.objects.bulk_create([
                BookingSeat(booking=booking, seat_id=sid, showtime=showtime)
                for sid in selected
            ])

            # 🔥 Save seats & booking id in session for payment page
            request.session["selected_seats"] = selected
            request.session["booking_id"] = str(booking.id)

        return redirect("movies:payment", showtime_id=showtime.id)

    # seat grid for display
    seat_grid = {}
    for s in seats:
        seat_grid.setdefault(s.row_number, {})[s.seat_number] = s

    max_col = seats.aggregate(max=Max("seat_number"))["max"] or 0

    context = {
        "seat_grid": seat_grid,
        "max_col_range": range(1, max_col + 1),
        "booked_seat_ids": booked_seat_ids,
        "showtime": showtime,
    }

    return render(request, "movies/booking.html", context)


@login_required
def payment_view(request, showtime_id):
    showtime = get_object_or_404(Showtime, id=showtime_id)

    selected_seat_ids = request.session.get("selected_seats", [])
    booking_id = request.session.get("booking_id")

    if not booking_id:
        messages.error(request, "Session expired. Please book again.")
        return redirect("movies:index")

    booking = Booking.objects.get(id=booking_id)

    # 🔥 Convert seat IDs → real Seat objects
    selected_seat_objects = Seat.objects.filter(id__in=selected_seat_ids).order_by("row_number", "seat_number")

    total_amount = int(float(booking.total_price) * 100)  # Razorpay uses paise

    if request.method == "POST":
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        razorpay_order = client.order.create({
            "amount": total_amount,
            "currency": "INR",
            "payment_capture": "1",
        })

        booking.razorpay_order_id = razorpay_order["id"]
        booking.save()

        return JsonResponse({
            "order_id": razorpay_order["id"],
            "amount": total_amount,
            "key": settings.RAZORPAY_KEY_ID,
            "booking_id": str(booking.id)
        })

    return render(request, "movies/payment.html", {
        "showtime": showtime,
        "seats": selected_seat_objects,
        "total_price": booking.total_price,
        "amount": total_amount,
        "booking_id": booking.id
    })

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related("showtime__movie").prefetch_related("booking_seats__seat").order_by("-booking_date")
    return render(request, "movies/bookings.html", {"bookings": bookings})

def login_view(request):
    if request.user.is_authenticated:
        return redirect("movies:index")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("movies:index")
    return render(request, "movies/auth_login.html", {"form": form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect("movies:index")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        # create profile
        user.profile.full_name = form.cleaned_data.get("full_name","")
        user.profile.save()
        login(request, user)
        return redirect("movies:index")
    return render(request, "movies/auth_register.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("movies:index")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("movies:index")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.username = user.email
        user.save()

        Profile.objects.create(
            user=user,
            full_name=form.cleaned_data.get("full_name", "")
        )

        login(request, user)
        return redirect("movies:index")

    return render(request, "movies/auth_register.html", {"form": form})


def payment_success(request):
    booking_id = request.GET.get("booking_id")
    payment_id = request.GET.get("payment_id")
    order_id = request.GET.get("order_id")
    signature = request.GET.get("signature")

    booking = Booking.objects.get(id=booking_id)

    booking.razorpay_payment_id = payment_id
    booking.razorpay_order_id = order_id
    booking.razorpay_signature = signature
    booking.status = "confirmed"
    booking.save()

    messages.success(request, "Payment successful! Booking confirmed.")
    return redirect("movies:bookings")