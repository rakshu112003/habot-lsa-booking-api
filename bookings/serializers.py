from rest_framework import serializers

from .models import (
    Parent,
    LSA_Profile,
    Booking_Request,
    Booking,
    Payment,
)


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = "__all__"


class LSAProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LSA_Profile
        fields = "__all__"


class BookingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking_Request
        fields = "__all__"


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"