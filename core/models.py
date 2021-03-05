from django.conf import settings
from django.db import models
from django.urls import reverse


CATEGORY_CHOICES = (
    ('S', 'Shirt'),
    ('SW', 'Sports Wear'),
    ('OW', 'Out Wear'),
)

LABEL_CHOICES = (
    ('p', 'primary'),
    ('s', 'secondary'),
    ('d', 'danger'),
)


class Item(models.Model):
    title = models.CharField(max_length=100)
    discount_price = models.FloatField(blank=True, null=True)
    price = models.FloatField()
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    slug = models.SlugField()
    description = models.TextField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })
    
    def get_add_to_cart_url(self):
        return reverse("core:add_to_cart", kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    item = models.ForeignKey(Item, on_delete=models.CASCADE) 


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    order_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
