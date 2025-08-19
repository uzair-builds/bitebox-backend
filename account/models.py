from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from shortuuid.django_fields import ShortUUIDField



class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None,password2=None, latitude=None, longitude=None):
        """
        Creates and saves a User with the given email, name, tc, and password.
        """
        if not email:
            raise ValueError('User must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
          
            latitude=latitude,
            longitude=longitude
        )

        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        """
        Creates and saves a superuser with the given email, name, tc, and password.
        """
        user = self.create_user(
            email=email,
            password=password,
            name=name,
            
            latitude=None,  # Make latitude and longitude optional
            longitude=None
        )
        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)
        return user

# Custom User Model
class User(AbstractBaseUser):
    email = models.EmailField(verbose_name='Email', max_length=255, unique=True)
    username = models.CharField(max_length=50, unique=True, blank=True, null=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=25, null=True, blank=True)
    otp = models.CharField(max_length=100, null=True, blank=True)

    # Optional fields for location
    latitude = models.DecimalField(max_digits=15, decimal_places=10, blank=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        # Does the user have a specific permission? Only admins do
        return self.is_admin

    def has_module_perms(self, app_label):
        # Does the user have permissions to view the app `app_label`? Only admins do
        return self.is_admin

    @property
    def is_staff(self):
        # All admins are considered staff
        return self.is_admin

    # Overriding the save method
    def save(self, *args, **kwargs):
        email_username, _ = self.email.split('@')

        # Set name and username based on email if they are not provided
        if not self.name:
            self.name = email_username
        
        if not self.username:
            # Ensure username uniqueness by appending some identifier (optional, e.g., user ID or random number)
            self.username = email_username

        super(User, self).save(*args, **kwargs)

# Profile model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(null=True, blank=True, upload_to='profile/', default='profile/default.jpg')
    full_name = models.CharField(max_length=50, null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=150, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    pid = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefghijk")

    def __str__(self):
        return self.full_name if self.full_name else str(self.user.name)

    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = self.user.name
        super(Profile, self).save(*args, **kwargs)

# Signals to create or update Profile when User is created or saved
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
