
from rest_framework import serializers
from .models import DeliveryBoy, Restaurant,RestaurantRequest
from account.serializers import UserSerializer
class RestaurantCreateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Restaurant
        fields = '__all__'

    def validate(self, data):
        """
        Custom validation logic for creating a Restaurant
        """
        # Ensure that latitude and longitude are either both present or both absent
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if (latitude and not longitude) or (longitude and not latitude):
            raise serializers.ValidationError("Both latitude and longitude must be provided together.")

        # Validate operational hours (opening_time should be before closing_time)
        if data['opening_time'] >= data['closing_time']:
            raise serializers.ValidationError("Opening time must be earlier than closing time.")

        return data

        
    def __init__(self, *args, **kwargs):
        super(RestaurantCreateSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cart order, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3


    # def create(self, validated_data):
    #     """
    #     Create a new Restaurant instance
    #     """
    #     # Create the Restaurant object using the validated data
    #     restaurant = Restaurant.objects.create(**validated_data)
    #     return restaurant
    




class EarningSummarySerializer(serializers.Serializer):
    monthly_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)


class RestaurantRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantRequest
        fields = ['id', 'name', 'image', 'email', 'contact_no', 'description','status','latitude','longitude']
        read_only_fields = ['status']

class DeliveryBoySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryBoy
        fields = '__all__'