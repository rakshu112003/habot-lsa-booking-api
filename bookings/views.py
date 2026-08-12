import logging
import requests

from django.conf import settings
from django.db import transaction

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import (
    Parent,
    LSA_Profile,
    Booking_Request,
    Booking,
    Payment,
)

from .serializers import (
    ParentSerializer,
    LSAProfileSerializer,
    BookingRequestSerializer,
    BookingSerializer,
    PaymentSerializer,
)


logger = logging.getLogger(__name__)


# --------------------------------------------------
# PARENT
# --------------------------------------------------

class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer


# --------------------------------------------------
# LSA PROFILE
# --------------------------------------------------

class LSAProfileViewSet(viewsets.ModelViewSet):
    queryset = LSA_Profile.objects.all()
    serializer_class = LSAProfileSerializer

    @action(detail=False, methods=["get"], url_path="search")
    def search_lsa(self, request):

        skill = request.query_params.get(
            "skill", ""
        ).strip().lower()

        if not skill:
            return Response(
                {
                    "error": "skill query parameter is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        matching_lsas = []

        for lsa in LSA_Profile.objects.filter(
            is_available=True
        ):

            skills = lsa.get_skills_list()

            skills_lower = [
                str(skill_item).strip().lower()
                for skill_item in skills
            ]

            if skill in skills_lower:
                matching_lsas.append(lsa)

        serializer = self.get_serializer(
            matching_lsas,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# --------------------------------------------------
# BOOKING REQUEST
# --------------------------------------------------

class BookingRequestViewSet(viewsets.ModelViewSet):
    queryset = Booking_Request.objects.all()
    serializer_class = BookingRequestSerializer


# --------------------------------------------------
# BOOKING
# --------------------------------------------------

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        booking_request_id = request.data.get(
            "booking_request"
        )

        if not booking_request_id:
            return Response(
                {
                    "error": "booking_request required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking_request = (
                Booking_Request.objects
                .select_for_update()
                .get(id=booking_request_id)
            )

        except Booking_Request.DoesNotExist:

            return Response(
                {
                    "error": "Booking request not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if str(
            booking_request.status
        ).upper() == "CONFIRMED":

            return Response(
                {
                    "error": "Already confirmed"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        required_skill = str(
            booking_request.required_skill
        ).strip().lower()

        available_lsas = LSA_Profile.objects.filter(
            is_available=True
        )

        for lsa in available_lsas:

            skills = lsa.get_skills_list()

            skills_lower = [
                str(skill_item).strip().lower()
                for skill_item in skills
            ]

            if required_skill not in skills_lower:
                continue

            clash = Booking.objects.filter(
                lsa_profile=lsa,
                booking_date=booking_request.requested_date,
                booking_time=booking_request.requested_time,
                status__in=[
                    "CONFIRMED",
                    "PENDING"
                ],
            ).exists()

            if clash:
                continue

            booking = Booking.objects.create(
                booking_request=booking_request,
                lsa_profile=lsa,
                booking_date=booking_request.requested_date,
                booking_time=booking_request.requested_time,
                status="CONFIRMED",
            )

            booking_request.status = "CONFIRMED"

            booking_request.save(
                update_fields=["status"]
            )

            serializer = self.get_serializer(
                booking
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "error": (
                    "No available LSA "
                    "for this skill and time"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------
    # CANCEL BOOKING
    # --------------------------------------------------

    def destroy(self, request, *args, **kwargs):

        booking = self.get_object()

        if booking.status == "CANCELLED":

            return Response(
                {
                    "message": "Already cancelled"
                },
                status=status.HTTP_200_OK,
            )

        booking.status = "CANCELLED"

        booking.save(
            update_fields=["status"]
        )

        lsa = booking.lsa_profile

        lsa.is_available = True

        lsa.save(
            update_fields=["is_available"]
        )

        booking_request = booking.booking_request

        booking_request.status = "CANCELLED"

        booking_request.save(
            update_fields=["status"]
        )

        return Response(
            {
                "message": "Booking cancelled successfully.",
                "booking_id": booking.id,
            },
            status=status.HTTP_200_OK,
        )


# --------------------------------------------------
# PAYMENT
# --------------------------------------------------

class PaymentViewSet(viewsets.ModelViewSet):

    queryset = Payment.objects.all()

    serializer_class = PaymentSerializer

    @action(
        detail=False,
        methods=["post"],
        url_path="process"
    )
    def process_payment(self, request):

        booking_id = request.data.get(
            "booking"
        )

        amount = request.data.get(
            "amount"
        )

        if not booking_id:

            return Response(
                {
                    "error": "booking field is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount is None:

            return Response(
                {
                    "error": "amount field is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            booking = Booking.objects.get(
                id=booking_id
            )

        except Booking.DoesNotExist:

            return Response(
                {
                    "error": "Booking not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if Payment.objects.filter(
            booking=booking
        ).exists():

            return Response(
                {
                    "error": (
                        "Payment already exists "
                        "for this booking"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction_id = (
            f"TXN-{booking.id}-"
            f"{booking.booking_date}"
        )

        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            transaction_id=transaction_id,
            status="PENDING",
        )

        # Optional mock external payment service
        mock_url = getattr(
            settings,
            "MOCK_PAYMENT_URL",
            None
        )

        if mock_url:

            try:

                response = requests.post(
                    mock_url,
                    json={
                        "booking_id": booking.id,
                        "amount": str(amount),
                        "transaction_id": transaction_id,
                    },
                    timeout=5,
                )

                response.raise_for_status()

                data = response.json()

                if data.get("status") == "SUCCESS":

                    payment.status = "SUCCESS"

                    payment.save(
                        update_fields=["status"]
                    )

                    booking.status = "CONFIRMED"

                    booking.save(
                        update_fields=["status"]
                    )

                else:

                    payment.status = "FAILED"

                    payment.save(
                        update_fields=["status"]
                    )

            except requests.RequestException as error:

                logger.exception(
                    "Payment service failed: %s",
                    error
                )

                payment.status = "FAILED"

                payment.save(
                    update_fields=["status"]
                )

                return Response(
                    {
                        "error": (
                            "Payment service unavailable"
                        )
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        serializer = self.get_serializer(
            payment
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


# --------------------------------------------------
# PAYMENT WEBHOOK
# --------------------------------------------------

@api_view(["POST"])
def payment_webhook(request):

    transaction_id = request.data.get(
        "transaction_id"
    )

    payment_status = str(
        request.data.get(
            "status",
            ""
        )
    ).upper()

    if not transaction_id:

        return Response(
            {
                "error": (
                    "transaction_id is required"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if payment_status not in [
        "SUCCESS",
        "FAILED"
    ]:

        return Response(
            {
                "error": (
                    "status must be "
                    "SUCCESS or FAILED"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:

        payment = (
            Payment.objects
            .select_related("booking")
            .get(
                transaction_id=transaction_id
            )
        )

    except Payment.DoesNotExist:

        return Response(
            {
                "error": "Payment not found"
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    payment.status = payment_status

    payment.save(
        update_fields=["status"]
    )

    booking = payment.booking

    if payment_status == "SUCCESS":

        booking.status = "CONFIRMED"

    else:

        booking.status = "CANCELLED"

    booking.save(
        update_fields=["status"]
    )

    logger.info(
        "Payment webhook processed: %s -> %s",
        transaction_id,
        payment_status,
    )

    return Response(
        {
            "message": "Payment status updated",
            "transaction_id": transaction_id,
            "payment_status": payment.status,
            "booking_status": booking.status,
        },
        status=status.HTTP_200_OK,
    )