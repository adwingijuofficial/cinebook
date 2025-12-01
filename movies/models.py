# movies/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True)
    ROLE_CHOICES = (("user","User"),("admin","Admin"))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")

    def __str__(self):
        return self.full_name or self.user.email

class Movie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    poster_url = models.ImageField(upload_to='movies/',blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True, null=True)
    runtime = models.PositiveIntegerField(blank=True, null=True, help_text="minutes")
    release_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Screen(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Seat(models.Model):
    SEAT_TYPE = (("regular","Regular"),("vip","VIP"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name="seats")
    row_number = models.PositiveIntegerField()
    seat_number = models.PositiveIntegerField()
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPE, default="regular")

    class Meta:
        unique_together = ("screen","row_number","seat_number")
        ordering = ["row_number","seat_number"]

    def __str__(self):
        return f"{self.screen.name} - R{self.row_number}S{self.seat_number}"

class Showtime(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="showtimes")
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.movie.title} @ {self.start_time}"

class Booking(models.Model):
    STATUS_CHOICES = (("pending","Pending"),("confirmed","Confirmed"),("cancelled","Cancelled"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    booking_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Booking {self.id} - {self.user}"

class BookingSeat(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="booking_seats")
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT)
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("seat","showtime")