from django.db import models
from account.models import User
from django.utils.text import slugify
from django.core.validators import EmailValidator



class Restaurant(models.Model):
    # Basic information
    user = models.OneToOneField(User, on_delete=models.SET_NULL,null=True,default=1) 
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True,null=True, )
    image = models.ImageField(upload_to='restaurants/', blank=True)
    slug=models.SlugField(max_length=500)
    # Location tracking
    latitude = models.DecimalField(max_digits=9, decimal_places=6,blank=True,null=True,)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,blank=True,null=True,)
    address = models.CharField(max_length=255,blank=True,null=True,)
    city = models.CharField(max_length=100,blank=True,null=True,)
    state = models.CharField(max_length=100,blank=True,null=True,)
    zip_code = models.CharField(max_length=10,blank=True,null=True,)

    # Operational hours
    opening_time = models.TimeField(null=True,blank=True)
    closing_time = models.TimeField(null=True,blank=True)

    # Additional settings
    is_open = models.BooleanField(default=True)
    max_delivery_distance_km = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,blank=True,null=True,)  # Max distance for delivery in km

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"

    def save(self,*args, **kwargs):
        if self.slug==""or self.slug ==None:
            self.slug=slugify(self.name)
        super().save(*args, **kwargs)





class DeliveryBoy(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('in delivery', 'In Delivery'),
    ]
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, related_name='delivery_boys')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, validators=[EmailValidator()], null=True, blank=True)  # New field
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"







class RestaurantRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='restaurant_requests/')
    email = models.EmailField()
    contact_no = models.CharField(max_length=15)
    description = models.TextField(null=True,blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6,blank=True,null=True,)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,blank=True,null=True,)

    def __str__(self):
        return f"{self.name} - {self.status}"
