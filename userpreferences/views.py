from django.shortcuts import render
import os
import json
from django.conf import settings
from .models import UserPreference
from django.contrib import messages
# Create your views here.

# for handling the currency selection and budget 
def index(request):

    # initializing an empty list currency_data and setting the initial value of budget to 0
    currency_data = []
    budget = 0

    # reads data from a JSON file named 'currencies.json' located in the project's base directory
    # The data is loaded into the currency_data list as dictionaries containing 'name' and 'value' keys.
    file_path = os.path.join(settings.BASE_DIR, 'currencies.json')

    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        for k, v in data.items():
            currency_data.append({'name': k, 'value': v})

    # checks if a UserPreference object exists for the current user, if it does, the existing preferences are retrieved
    exists = UserPreference.objects.filter(user=request.user).exists()
    user_preferences = None
    if exists:
        user_preferences = UserPreference.objects.get(user=request.user)

    # When request method is 'GET', the code renders the 'preferences/index.html' template, 
    # passing along the currency data, user preferences, and budget as context
    if request.method == 'GET':

        return render(request, 'preferences/index.html', {'currencies': currency_data,
                                                          'user_preferences': user_preferences, 'budget': budget})
    
    # handles POST reuest
    else:
        currency = request.POST['currency']
        budget = request.POST['budget']

        # checks if a budget value is provided and if not, it adds an error message 
        if not budget:
            messages.error(request, 'Budget is required')
            return render(request, 'preferences/index.html', {'currencies': currency_data,
                                                          'user_preferences': user_preferences, 'budget': budget})
        
        # If preferences already exist for the user, the code updates the existing UserPreference object with the 
        # new currency and budget values and saves it. Otherwise, it creates a new UserPreference object.
        if exists:
            user_preferences.currency = currency
            user_preferences.budget = budget
            user_preferences.save()
        else:
            UserPreference.objects.create(user=request.user, currency=currency, budget=budget)
        messages.success(request, 'Changes saved')
        return render(request, 'preferences/index.html', {'currencies': currency_data, 'user_preferences': user_preferences, 'budget': budget})