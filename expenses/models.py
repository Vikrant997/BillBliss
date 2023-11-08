from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

# Create your models here.

# defines a Django model for representing expenses
class Expense(models.Model):
    amount = models.FloatField()
    date = models.DateField(default=now)
    description = models.TextField()
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE)
    category = models.CharField(max_length=266)

    # The __str__ method is defined to provide a human-readable string representation of an expense object. 
    # In this case, it returns the category of the expense.
    def __str__(self):
        return self.category

    # The Meta class inside the Expense model is used to define metadata for the model. In this case, it specifies the default ordering for 
    # the expenses. The expenses will be ordered by the date field.
    class Meta:
        ordering: ['-date']


# defines a Django model for representing categories of expenses
class Category(models.Model):
    name = models.CharField(max_length=255)

    # specifies that the plural name of the model in the Django admin should be 'Categories'
    class Meta:
        verbose_name_plural = 'Categories'

    # it returns the name of the category
    def __str__(self):
        return self.name