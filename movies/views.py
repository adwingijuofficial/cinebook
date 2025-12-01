# movies/views.py
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

from movies import models

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
    seats = Seat.objects.filter(screen=screen).order_by("row_number","seat_number")
    # booked seats for this showtime
    booked_seat_ids = set(BookingSeat.objects.filter(showtime=showtime).values_list("seat_id", flat=True))

    # derive rows and cols
    rows = seats.values_list("row_number", flat=True).distinct().order_by("row_number")
    max_col = seats.aggregate(max=Max("seat_number"))["max"] or 0

    if request.method == "POST":
        selected = request.POST.getlist("seats")  # list of seat ids
        if not selected:
            messages.error(request, "Please select at least one seat")
            return redirect(request.path)
        # transaction to avoid double-book
        with transaction.atomic():
            # check seat availability again
            already_booked = BookingSeat.objects.select_for_update().filter(showtime=showtime, seat_id__in=selected).exists()
            if already_booked:
                messages.error(request, "One or more seats were just booked by someone else. Please try again.")
                return redirect(request.path)
            total_price = showtime.price * len(selected)
            booking = Booking.objects.create(user=request.user, showtime=showtime, total_price=total_price, status="pending")
            BookingSeat.objects.bulk_create([
                BookingSeat(booking=booking, seat_id=sid, showtime=showtime) for sid in selected
            ])
            messages.success(request, "Booking successful (pending).")
            return redirect("movies:bookings")

# prepare seat grid for template
    seat_grid = {}
    for s in seats:
        seat_grid.setdefault(s.row_number, {})[s.seat_number] = s

    max_col = seats.aggregate(max=Max("seat_number"))["max"] or 0
    max_col_range = range(1, max_col + 1)

    context = {
    "seat_grid": seat_grid,
    "max_col_range": max_col_range,
    "booked_seat_ids": booked_seat_ids,  # FIXED
    "showtime": showtime,
}

    return render(request, "movies/booking.html", context)

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