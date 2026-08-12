from django.db import models
from django.contrib.auth.models import User


class Parent(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )
    address = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        if self.user:
            return self.user.username
        return f"Parent {self.id}"


class LSA_Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    bio = models.TextField(
        blank=True,
        null=True
    )
    skills = models.TextField(
        default="[]",
        blank=True
    )
    experience_years = models.IntegerField(
        default=0
    )
    is_available = models.BooleanField(
        default=True
    )

    def get_skills_list(self):
        import json

        try:
            return json.loads(self.skills)
        except (json.JSONDecodeError, TypeError):
            return [
                s.strip()
                for s in self.skills.split(",")
                if s.strip()
            ]

    def __str__(self):
        if self.user:
            return f"LSA: {self.user.username}"
        return f"LSA {self.id}"


class Booking_Request(models.Model):
    STATUS = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]

    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name="booking_requests"
    )
    required_skill = models.CharField(
        max_length=100
    )
    requested_date = models.DateField()
    requested_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="PENDING"
    )

    def __str__(self):
        return f"Request {self.id} - {self.required_skill}"


class Booking(models.Model):
    STATUS = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]

    booking_request = models.OneToOneField(
        Booking_Request,
        on_delete=models.CASCADE,
        related_name="booking"
    )
    lsa_profile = models.ForeignKey(
        LSA_Profile,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    booking_date = models.DateField()
    booking_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="CONFIRMED"
    )

    def __str__(self):
        return f"Booking {self.id}"


class Payment(models.Model):
    STATUS = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="payment"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="PENDING"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Payment {self.id} - {self.status}"