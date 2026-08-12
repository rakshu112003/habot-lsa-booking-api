from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ParentViewSet,
    LSAProfileViewSet,
    BookingRequestViewSet,
    BookingViewSet,
    PaymentViewSet,
    payment_webhook,
)


# Webhook BEFORE router URLs
urlpatterns = [
    path(
        "payments/webhook/",
        payment_webhook,
        name="payment-webhook",
    ),
]


router = DefaultRouter()

router.register("parents", ParentViewSet)
router.register("lsa-profiles", LSAProfileViewSet)
router.register("booking-requests", BookingRequestViewSet)
router.register("bookings", BookingViewSet)
router.register("payments", PaymentViewSet)


urlpatterns += router.urls