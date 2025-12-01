# movies/admin.py
from django.contrib import admin
from .models import Profile, Movie, Screen, Seat, Showtime, Booking, BookingSeat

admin.site.register(Profile)
admin.site.register(Movie)
admin.site.register(Screen)
admin.site.register(Seat)
admin.site.register(Showtime)
admin.site.register(Booking)
admin.site.register(BookingSeat)