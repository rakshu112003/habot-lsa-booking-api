from datetime import date, time

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import (
    Parent,
    LSA_Profile,
    Booking_Request,
    Booking,
    Payment,
)


class BookingAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testparent",
            password="test123"
        )

        self.parent = Parent.objects.create(
            user=self.user,
            phone="9876543210"
        )

        self.lsa_user = User.objects.create_user(
            username="testlsa",
            password="test123"
        )

        self.lsa = LSA_Profile.objects.create(
            user=self.lsa_user,
            skills='["Math", "English"]',
            is_available=True,
            experience_years=3
        )

    # 1. LSA search success
    def test_lsa_search_by_skill(self):
        response = self.client.get(
            "/api/lsa-profiles/search/?skill=math"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    # 2. LSA search without skill
    def test_lsa_search_without_skill(self):
        response = self.client.get(
            "/api/lsa-profiles/search/"
        )

        self.assertEqual(response.status_code, 400)

    # 3. Create booking request
    def test_create_booking_request(self):
        response = self.client.post(
            "/api/booking-requests/",
            {
                "parent": self.parent.id,
                "required_skill": "Math",
                "requested_date": "2026-08-20",
                "requested_time": "10:00:00",
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["status"],
            "PENDING"
        )

    # 4. Create booking successfully
    def test_create_booking(self):
        booking_request = Booking_Request.objects.create(
            parent=self.parent,
            required_skill="Math",
            requested_date=date(2026, 8, 20),
            requested_time=time(10, 0),
            status="PENDING"
        )

        response = self.client.post(
            "/api/bookings/",
            {
                "booking_request": booking_request.id
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["status"],
            "CONFIRMED"
        )

    # 5. Prevent double booking
    def test_prevent_double_booking(self):
        booking_request_1 = Booking_Request.objects.create(
            parent=self.parent,
            required_skill="Math",
            requested_date=date(2026, 8, 21),
            requested_time=time(10, 0),
            status="PENDING"
        )

        response1 = self.client.post(
            "/api/bookings/",
            {
                "booking_request": booking_request_1.id
            },
            format="json"
        )

        self.assertEqual(response1.status_code, 201)

        booking_request_2 = Booking_Request.objects.create(
            parent=self.parent,
            required_skill="Math",
            requested_date=date(2026, 8, 21),
            requested_time=time(10, 0),
            status="PENDING"
        )

        response2 = self.client.post(
            "/api/bookings/",
            {
                "booking_request": booking_request_2.id
            },
            format="json"
        )

        self.assertEqual(response2.status_code, 400)

    # 6. Payment webhook success
    def test_payment_webhook_success(self):
        booking_request = Booking_Request.objects.create(
            parent=self.parent,
            required_skill="Math",
            requested_date=date(2026, 8, 22),
            requested_time=time(11, 0),
            status="CONFIRMED"
        )

        booking = Booking.objects.create(
            booking_request=booking_request,
            lsa_profile=self.lsa,
            booking_date=date(2026, 8, 22),
            booking_time=time(11, 0),
            status="CONFIRMED"
        )

        Payment.objects.create(
            booking=booking,
            amount=500,
            transaction_id="TEST-WEBHOOK-001",
            status="PENDING"
        )

        response = self.client.post(
            "/api/payments/webhook/",
            {
                "transaction_id": "TEST-WEBHOOK-001",
                "status": "SUCCESS"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["payment_status"],
            "SUCCESS"
        )

    # 7. Payment webhook failure
    def test_payment_webhook_failure(self):
        booking_request = Booking_Request.objects.create(
            parent=self.parent,
            required_skill="Math",
            requested_date=date(2026, 8, 23),
            requested_time=time(11, 0),
            status="CONFIRMED"
        )

        booking = Booking.objects.create(
            booking_request=booking_request,
            lsa_profile=self.lsa,
            booking_date=date(2026, 8, 23),
            booking_time=time(11, 0),
            status="CONFIRMED"
        )

        Payment.objects.create(
            booking=booking,
            amount=500,
            transaction_id="TEST-WEBHOOK-002",
            status="PENDING"
        )

        response = self.client.post(
            "/api/payments/webhook/",
            {
                "transaction_id": "TEST-WEBHOOK-002",
                "status": "FAILED"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["payment_status"],
            "FAILED"
        )
        self.assertEqual(
            response.data["booking_status"],
            "CANCELLED"
        )