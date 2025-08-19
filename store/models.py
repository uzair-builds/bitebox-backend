from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.text import slugify 
from account.models import User,Profile
from restaurants.models import Restaurant
from django.dispatch import receiver
import uuid
from django.db.models.signals import post_save
# Create your models here.
class Category(models.Model):
    title=models.CharField(max_length=100)
    image=models.FileField(upload_to="categories",default="category.jpg",null=True,blank=True)
    active=models.BooleanField(default=True)
    slug=models.SlugField(unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural="Categories"
        ordering=['-title']

    def save(self,*args, **kwargs):
        if self.slug == "" or self.slug == None:
            self.slug=slugify(self.title)
        super(Category,self).save(*args, **kwargs)

STATUS = (
    ("draft", "Draft"),
    ("disabled", "Disabled"),
    ("in_review", "In Review"),
    ("published", "Published"),
)

class Dish(models.Model):  # Renamed from Product to Dish
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to="dishes", default="dish.jpg", null=True, blank=True)  # Changed upload path
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(decimal_places=2, max_digits=12, default=0.00)
    old_price = models.DecimalField(decimal_places=2, max_digits=12, default=0.00)
    tags = models.CharField(max_length=1000, null=True, blank=True)
    stock_qty = models.PositiveIntegerField(default=1)
    in_stock = models.BooleanField(default=True)
    status = models.CharField(max_length=100, choices=STATUS, default="published")
    featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    rating = models.IntegerField(default=0, null=True, blank=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    did = ShortUUIDField(unique=True, length=10, alphabet="abcdefg12345")
    slug = models.SlugField(unique=True,null=True,blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

    def dish_rating(self):
        dish_rating=Review.objects.filter(dish=self).aggregate(avg_rating=models.Avg("rating"))
        return dish_rating['avg_rating']

    def rating_count(self):
        rating_count=Review.objects.filter(dish=self).count()
        return rating_count

    def gallery(self):
        return Gallery.objects.filter(dish=self)

    def specification(self):
        return Specification.objects.filter(dish=self)

    def spice_level(self):
        return SpiceLevel.objects.filter(dish=self)

    def portion_size(self):
        return PortionSize.objects.filter(dish=self)
    
    def orders(self):
        return CartOrderItem.objects.filter(dish=self).count()

    # def save(self,*args, **kwargs):
    #     if self.slug == "" or self.slug == None:
    #         self.slug=slugify(self.title)
    #     super(Dish,self).save(*args, **kwargs)
    #     self.rating=self.dish_rating()
    #     super(Dish,self).save(*args, **kwargs)
    def save(self, *args, **kwargs):
        if not self.slug:  # Simplified slug check
            self.slug = slugify(self.title)

        is_new = self.pk is None  # Check if the object is new

        super(Dish, self).save(*args, **kwargs)  # ✅ First save to assign primary key

        if not is_new:  # Avoid querying related objects before saving
            self.rating = self.dish_rating()
            super(Dish, self).save(update_fields=["rating"])  # ✅ Only update rating



class PortionSize(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.SET_NULL,null=True, related_name='portion_sizes')
    size_name = models.CharField(max_length=50,null=True,blank=True)  # e.g., "Small", "Medium", "Large"
    price = models.DecimalField(decimal_places=2, max_digits=12,null=True,blank=True)  # Price for the specific portion size

    def __str__(self):
        return f"{self.size_name} for {self.dish.title}"
    def get_price_by_portion(self, portion):
        try:
            portion = PortionSize.objects.filter(size_name=portion).first()
            return portion.price
        except PortionSize.DoesNotExist:
            return None
    

class SpiceLevel(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.SET_NULL,null=True, related_name='spice_levels')
    level_name = models.CharField(max_length=50,null=True,blank=True)  # e.g., "Mild", "Medium", "Spicy"
    additional_price = models.DecimalField(decimal_places=2, max_digits=12, default=0.00,null=True,blank=True)  # Optional extra charge for spicier versions

    def __str__(self):
        return f"{self.level_name} for {self.dish.title}"


class  Gallery(models.Model):
    dish=models.ForeignKey(Dish,on_delete=models.SET_NULL,null=True)
    image=models.FileField(upload_to="dish_images",default="dish.jpg",null=True,blank=True)
    active=models.BooleanField(default=True)
    gid=ShortUUIDField(unique=True,length=10,alphabet="abcdefgh12345")

    def __str__(self):
        return self.dish.title
    class Meta:
        verbose_name_plural="Dish Images"


class Specification(models.Model):
    dish=models.ForeignKey(Dish,on_delete=models.SET_NULL,null=True)
    title=models.CharField(max_length=100,null=True,blank=True)
    content=models.CharField(max_length=1000,null=True,blank=True)
    
    
    def __str__(self):
        return self.title
    

class Cart(models.Model):
    dish=models.ForeignKey(Dish,on_delete=models.CASCADE)
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    qty=models.PositiveIntegerField(default=0)
    price=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    sub_total=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    service_fee=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    tax_fee=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    total=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    country=models.CharField(max_length=100,null=True,blank=True)
    portion_size=models.CharField(max_length=100,null=True,blank=True)
    spice_level=models.CharField(max_length=100,null=True,blank=True)
    cart_id=models.CharField(max_length=100,null=True,blank=True)
    date=models.DateTimeField(auto_now_add=True)
    is_voice_item = models.BooleanField(default=False)   # NEW
    
    def __str__(self):
        return f"{self.cart_id}-{self.dish.title}"
    class Meta:
        ordering=['-id']
    def price_by_portion_size(self):
        portion = PortionSize.objects.filter(size_name=self.portion_size).first()
        return portion.price if portion else None



class CartOrder(models.Model):
    PAYMENT_STATUS=(
    ("paid", "Paid"),
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("cancelled", "Cancelled"),
       )    
    ORDER_STATUS=(
    ("pending", "Pending"),
    ("fulfilled", "Fulfilled"),
    ("cancelled", "Cancelled"),
       )    
    restaurant=models.ManyToManyField(Restaurant,blank=True)
    buyer=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    sub_total=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    service_fee=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    tax_fee=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    total=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    payment_status=models.CharField(choices=PAYMENT_STATUS,default="pending",max_length=100)
    order_status=models.CharField(choices=ORDER_STATUS,default="pending",max_length=100)
    #Coupon
    initial_total=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    saved=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    #Bio data
    full_name=models.CharField(max_length=100,null=True,blank=True)
    email=models.CharField(max_length=100,null=True,blank=True)
    mobile=models.CharField(max_length=100,null=True,blank=True)


    address=models.CharField(max_length=100,null=True,blank=True)
    city=models.CharField(max_length=100,null=True,blank=True)
    state=models.CharField(max_length=100,null=True,blank=True)
    country=models.CharField(max_length=100,null=True,blank=True)
    oid=ShortUUIDField(unique=True,length=10,alphabet="abcdefg12345")
    date=models.DateTimeField(auto_now_add=True)
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.oid
    
    def orderitem(self):
        return CartOrderItem.objects.filter(order=self)


class CartOrderItem(models.Model):
    order=models.ForeignKey(CartOrder,on_delete=models.CASCADE)
    qty=models.PositiveIntegerField(default=0)
    price=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    sub_total=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    service_fee=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    tax_fee=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    total=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    country=models.CharField(max_length=100,null=True,blank=True)
    portion_size=models.CharField(max_length=100,null=True,blank=True)
    spice_level=models.CharField(max_length=100,null=True,blank=True)

    initial_total=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)
    saved=models.DecimalField(default=0.00,max_digits=12,decimal_places=2)

    dish=models.ForeignKey(Dish,on_delete=models.CASCADE)
    restaurant=models.ForeignKey(Restaurant,on_delete=models.CASCADE)
    
    oid=ShortUUIDField(unique=True,length=10,alphabet="abcdefg12345")
    date=models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return self.oid
    
 

class DishFAQ(models.Model):
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    dish=models.ForeignKey(Dish,on_delete=models.CASCADE)
    email=models.EmailField(null=True)
    question=models.CharField(max_length=100)
    answer=models.TextField(null=True,blank=True)
    active=models.BooleanField(default=True)
    date=models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.question
    class Meta:
        verbose_name_plural="Dish FAQs"
        

class Review(models.Model):
    RATING_CHOICES=(
        (1,"1 star"),
        (2,"2 star"),
        (3,"3 star"),
        (4,"4 star"),
        (5,"5 star"),
    )
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    dish=models.ForeignKey(Dish,on_delete=models.SET_NULL,null=True,blank=True,related_name='reviews')
    review=models.TextField()
    reply=models.TextField(null=True,blank=True)
    rating=models.IntegerField(default=None,choices=RATING_CHOICES)
    active=models.BooleanField(default=True)
    date=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.dish.title
    class Meta:
        verbose_name_plural="Dish Reviews"

    def profile(self):
        return Profile.objects.get(user=self.user)



@receiver(post_save,sender=Review)
def update_dish_rating(sender,instance, **kwargs):
    if instance.dish:
        instance.dish.save()


class Wishlist(models.Model):
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    dish=models.ForeignKey(Dish,on_delete=models.CASCADE)
    date=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.dish.title

class Notification(models.Model):
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    restaurant=models.ForeignKey(Restaurant,on_delete=models.SET_NULL,null=True,blank=True)
    order=models.ForeignKey(CartOrder,on_delete=models.SET_NULL,null=True,blank=True)
    order_item=models.ForeignKey(CartOrderItem,on_delete=models.SET_NULL,null=True,blank=True)
    seen=models.BooleanField(default=False)
    date=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.order:
            return self.order.oid
        else:
            return f"Notification-{self.pk}"

class Coupon(models.Model):
    restaurant=models.ForeignKey(Restaurant,on_delete=models.CASCADE)
    used_by=models.ManyToManyField(User,blank=True)
    code=models.CharField(max_length=100)
    discount=models.PositiveIntegerField(default=1)
    active=models.BooleanField(default=False)
    date=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.code
    

class Tax(models.Model):
    country=models.CharField(max_length=100)
    rate=models.IntegerField(default=5,help_text="Rate is in the percentage e.g 5%")
    date=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.country



class Tag(models.Model):
    # Tag title
    title = models.CharField(max_length=30)
    # Category associated with the tag
    category = models.ForeignKey(Category, default="", verbose_name="Category", on_delete=models.PROTECT)
    # Is the tag active?
    active = models.BooleanField(default=True)
    # Unique slug for SEO-friendly URLs
    slug = models.SlugField("Tag slug", max_length=30, null=False, blank=False, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Tags"
        ordering = ('title',)