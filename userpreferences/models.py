from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserPreference(models.Model):

    # defines a field named user of type OneToOneField, It establishes a one-to-one relationship with the built-in User model in Django
    # on_delete=models.CASCADE argument specifies that if the associated user is deleted, 
    # the corresponding UserPreference object should be deleted as well
    user = models.OneToOneField(to = User, on_delete= models.CASCADE)
    currency = models.CharField(max_length=255, blank=True, null= True)
    
    
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null= True)
    language = models.CharField(max_length=10, choices=[('en', 'English'), ('sw', 'Swahili')], default='en')

    # returns a string representation of the UserPreference instance
    def __str__(self):
        return str(self.user)+'s' + 'preferences'  # str converts the associated user (self.user) to a string. 
    #The str() function is used here to ensure that the username (or whatever is returned by the __str__ method of the User model) 
    # is treated as a string
    



