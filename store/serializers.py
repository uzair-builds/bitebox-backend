from rest_framework import serializers

from account.serializers import ProfileSerializer 
from .models import Category,Dish,Gallery,Specification,PortionSize,SpiceLevel,Cart,CartOrder,CartOrderItem,Review,Wishlist,Coupon,Notification,DishFAQ
from restaurants.models import Restaurant

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields="__all__"
    

class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model=Gallery
        fields="__all__"

class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Specification
        fields="__all__"


class PortionSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model=PortionSize
        fields="__all__"


class SpiceLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model=SpiceLevel
        fields="__all__"

class ReviewSerializer(serializers.ModelSerializer):
    profile=ProfileSerializer()
    class Meta:
        model=Review
        fields=['id','user','dish','review','rating','profile','date','reply']

    def __init__(self,*args, **kwargs):
        # super(ReviewSerializer,self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3

class DishSerializer(serializers.ModelSerializer):
    gallery=GallerySerializer(many=True,read_only=True)
    spice_level=SpiceLevelSerializer(many=True,read_only=True)
    specification=SpecificationSerializer(many=True,read_only=True)
    portion_size=PortionSizeSerializer(many=True,read_only=True)
    reviews=ReviewSerializer(many=True,read_only=True)

    #For telling react that these are the inline in the django,these are the same names which are in the model methods of product
    class Meta:
        model=Dish
        fields=['id','title','image','description','category','price','old_price','orders','stock_qty','in_stock','status','featured','views',
                # 'rating',
                'restaurant','gallery','specification','spice_level','portion_size','did','slug','date','dish_rating','reviews','rating_count']
    def __init__(self,*args, **kwargs):
        super(DishSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3
            

class CartSerializer(serializers.ModelSerializer):
    price_by_portion_size = serializers.SerializerMethodField()
    class Meta:
        model=Cart
        fields="__all__"
    def get_price_by_portion_size(self, obj):
        return obj.price_by_portion_size()

    def __init__(self,*args, **kwargs):
        super(CartSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3
            


class CartOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=CartOrderItem
        fields="__all__"

    def __init__(self,*args, **kwargs):
        super(CartOrderItemSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3

class CartOrderSerializer(serializers.ModelSerializer):
    orderitem=CartOrderItemSerializer(many=True,read_only=True)
    class Meta:
        model=CartOrder
        fields="__all__"

    def __init__(self,*args, **kwargs):
        super(CartOrderSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3
        
class DishFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model=DishFAQ
        fields="__all__"

    def __init__(self,*args, **kwargs):
        super(DishFAQSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model=Restaurant
        fields="__all__"

    def __init__(self,*args, **kwargs):
        super(RestaurantSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3


class ReviewSerializer(serializers.ModelSerializer):
    profile=ProfileSerializer()
    class Meta:
        model=Review
        fields=['id','user','dish','review','rating','profile','date','reply']

    def __init__(self,*args, **kwargs):
        super(ReviewSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model=Wishlist
        fields="__all__"

    def __init__(self,*args, **kwargs):
        super(WishlistSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model=Coupon
        fields="__all__"

    def __init__(self,*args, **kwargs):
        super(CouponSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Notification
        fields="__all__"

    def __init__(self,*args, **kwargs):
        super(NotificationSerializer,self).__init__(*args, **kwargs)
        request=self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth=0
        else:
            self.Meta.depth=3


class SummarySerializer(serializers.Serializer):
    dishes=serializers.IntegerField()
    orders=serializers.IntegerField()
    revenue=serializers.DecimalField(max_digits=12,decimal_places=2)

    
class CouponSummarySerializer(serializers.Serializer):
    total_coupons=serializers.IntegerField()
    active=serializers.IntegerField()


class NotificationSummarySerializer(serializers.Serializer):
    unread_notifications=serializers.IntegerField()
    read_notifications=serializers.IntegerField()
    all_notifications=serializers.IntegerField()

    

    