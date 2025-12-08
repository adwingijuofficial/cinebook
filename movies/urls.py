from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "movies"

urlpatterns = [
    path("", views.index, name="index"),

    path("movie/<uuid:movie_id>/", views.movie_detail, name="movie_detail"),
    path("booking/<uuid:showtime_id>/", views.booking_view, name="booking"),
    path("bookings/", views.my_bookings, name="bookings"),
    path("payment/<uuid:showtime_id>/", views.payment_view, name="payment"),
    path("payment/success/", views.payment_success, name="payment_success"),

    # ✅ AUTH ROUTES
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)