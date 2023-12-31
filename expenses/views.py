from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Category, Expense
# Create your views here.
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import json
from django.http import JsonResponse, HttpResponse
from userpreferences.models import UserPreference
import datetime
import csv
import xlwt
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from django.db.models import Sum
import os

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.utils import translation
from django.utils.translation import activate, get_language
import logging
from django.db.models import F
from django.db.models.functions import Coalesce

from decimal import Decimal

# This view is designed to respond to POST requests. It checks if the incoming request method is 'POST' before proceeding with the search.
def search_expenses(request):
    if request.method == 'POST':

        # extracts the search text from the JSON data in the request body
        # This assumes that the search text is sent as JSON with the key 'searchText'.
        search_str = json.loads(request.body).get('searchText')

        # performs a search on the Expense model using multiple criteria 
        # The filter method is used to construct a query that searches for expenses 
        # amount starts with the provided search string (amount__istartswith), same for others
        expenses = Expense.objects.filter(
            amount__istartswith = search_str, owner=request.user) | Expense.objects.filter(
            date__istartswith = search_str, owner=request.user) | Expense.objects.filter(
            description__icontains = search_str, owner=request.user) | Expense.objects.filter(
            category__icontains = search_str, owner=request.user)
        
        # retrieves the values of the filtered expenses
        # values method is used to get a QuerySet of dictionaries representing the expenses
        data = expenses.values()

        # converts the QuerySet of dictionaries into a JSON response
        # The JsonResponse is used to serialize the data and send it back as a JSON response
        return JsonResponse(list(data), safe=False)

# responsible for rendering the main expenses page, displaying a list of expenses along with some additional information
@login_required(login_url='/authentication/login')
def index(request):
    
    # retrieves all the categories from the Category model
    categories = Category.objects.all()

    # filters expenses based on the currently logged-in user
    # model has a field named owner that references the user who created the expense
    expenses = Expense.objects.filter(owner=request.user)


    order_option = request.GET.get('orderOption', 'date_increasing') 
    # Apply filtering and ordering to the expenses
    expenses = filter_and_order_expenses(expenses, order_option)

    # It sets up pagination for the expenses. It uses the Paginator class to paginate the expenses, displaying 5 expenses per page. 
    # The current page number is extracted from the request's GET parameters.
    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)

    # retrieves the user's currency and budget preferences from the UserPreference model
    currency = UserPreference.objects.filter(user=request.user).first()
    if currency:
        currency = currency.currency
    budget = UserPreference.objects.filter(user=request.user).first()
    if budget:
        budget = budget.budget
    

    # creates a context dictionary containing the expenses, the paginated page object, the user's currency preference, and the budget
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency,
        'budget': budget
    }

    # renders the 'expenses/index.html' template with the provided context
    return render(request, 'expenses/index.html', context)


def filter_and_order_expenses(queryset, order_option):
    # Define a dictionary to map order options to corresponding fields in the Expense model
    order_mapping = {
        'amount_increasing': 'amount',
        'amount_decreasing': '-amount',
        'date_increasing': 'date',
        'date_decreasing': '-date',
        'category_increasing': 'category',
        'category_decreasing': '-category',
        # Add more options as needed
    }
    
    # Apply ordering based on the order option
    if order_option:
        queryset = queryset.order_by(order_mapping.get(order_option, 'date'))

    return queryset




@login_required(login_url='/authentication/login')
def add_expense(request):

    # retrieves all categories from the Category model and creates a context dictionary containing these categories and the values
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'values': request.POST,
    }

    # If the request method is 'GET', the view renders the 'expenses/add_expense.html' template with the provided context. 
    # This is the initial rendering of the form.
    if request.method == 'GET':
        return render(request, 'expenses/add_expense.html', context)

    # the view extracts the amount, description, date, and category from the POST data
    if request.method == 'POST':
        amount = request.POST['amount']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/add_expense.html', context)
        description = request.POST['description']
        date = request.POST['expense_date']
        category = request.POST['category']
        

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'expenses/add_expense.html', context)

        if not category:
            messages.error(request, 'Category is required')
            return render(request, 'expenses/add_expense.html', {'categories': categories})

        # Check if the selected/entered category is a predefined category
        category, created = Category.objects.get_or_create(name=category)

        # If the category was not predefined and is a new user-defined category,
        # save it in the database for future use
        if created:
            category.save()

        # creates a new Expense object in the database with the provided details, associating it with the currently logged-in user
        Expense.objects.create(owner=request.user, amount=amount, date=date,
                               category=category, description=description)
        
        
        # calculates total expense
        total_expenses = Expense.objects.filter(owner=request.user).aggregate(Sum('amount'))['amount__sum']

        # Check if total expenses exceed the budget
        if total_expenses is not None and total_expenses > UserPreference.objects.get(user=request.user).budget:

            # Send email notification if budget_limit is crossed
            send_notification_email(request.user, total_expenses, UserPreference.objects.get(user=request.user).budget)
            messages.warning(request, f"Total expenses ({total_expenses}) exceed the budget ({UserPreference.objects.get(user=request.user).budget})!")

        messages.success(request, 'Expense saved successfully')
        return redirect('expenses')
    


# to check whether the user's total expenses exceed their budget
@csrf_exempt  # Only for demonstration. Consider using CSRF protection in production, means that it is exempt from CSRF (Cross-Site Request Forgery) protection
def check_budget_status(request):

    # calculates the total expenses for the currently logged-in user
    total_expenses = Expense.objects.filter(owner=request.user).aggregate(Sum('amount'))['amount__sum']

    # checks if the total expenses exceed the user's budget and creates a boolean variable budget_exceeded
    budget_exceeded = total_expenses is not None and total_expenses > UserPreference.objects.get(user=request.user).budget

    # returns a JSON response containing the result of the budget check.
    # The JSON response includes a key-value pair where the key is 'budget_exceeded' and the value is the boolean variable budget_exceeded.
    # This information can be used in frontend applications or other parts of the system to dynamically update the user interface based 
    # on the budget status.
    return JsonResponse({
        'budget_exceeded': budget_exceeded,
    })   


# This is a placeholder for the notification function. You'll need to implement it based on your notification system.
def send_notification_email(user, total_expenses, budget):

    # Implement your notification logic here
    subject = 'Expense Notification'
    html_message = render_to_string('expenses/notification_email.html', {'total_expenses': total_expenses, 'budget': budget})
    plain_message = strip_tags(html_message)
    from_email = 'viki99viki@gmail.com'  # Replace with your email
    recipient_list = [user.email]

    email = EmailMultiAlternatives(subject, plain_message, from_email, recipient_list)
    email.attach_alternative(mark_safe(html_message), "text/html")
    email.send()


# to update expenses
@login_required(login_url='/authentication/login')
def expense_edit(request, id):

    # retrieves the expense with the given primary key (id) from the database
    # also fetches all expense categories and creates a context dictionary containing the expense, its values, and the categories
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    context = {
        'expense': expense,
        'values': expense,
        'categories': categories
    }
    
    # If the request method is 'GET', the view renders the 'expenses/edit-expense.html' template with the provided context
    if request.method == 'GET':
        return render(request, 'expenses/edit-expense.html', context)
    
    # view extracts the updated amount, description, date, and category from the submitted form data
    if request.method == 'POST':
        amount = request.POST['amount']
        print("Values before rendering template:", request.POST)

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/edit-expense.html', context)
        description = request.POST['description']
        date = request.POST['expense_date']
        #category = request.POST['category']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'expenses/edit-expense.html', context)
        
        # Extract both the predefined category and the custom category fields
        category_name = request.POST['category']
        custom_category_name = request.POST['custom_category']
        
        # Check if the selected category is 'custom'
        if category_name == 'custom' and custom_category_name:
            
            # If the category is 'custom' and a custom category is provided, use the custom category
            category, created = Category.objects.get_or_create(name=custom_category_name)
            if created:
                print(f"New category created: {custom_category_name}")
                category.save()

        else:
            # If a predefined category is selected, use it
            category, created = Category.objects.get_or_create(name=category_name)

        # updates the expense object with the new values and saves it to the database
        expense.owner = request.user
        expense.amount = amount
        expense. date = date
        expense.category = category.name
        expense.description = description

        expense.save()
        messages.success(request, 'Expense updated  successfully')

        return redirect('expenses')

# handles the deletion of an existing expense
# This view function takes the request and the primary key (id) of the expense to be deleted as parameters
def delete_expense(request, id):

    # retrieves the expense with the given primary key (id) from the database
    expense = Expense.objects.get(pk=id)

    # deletes the expense from the database
    expense.delete()
    messages.success(request, 'Expense removed')

    # it redirects the user to the 'expenses' page after deleting the expense
    return redirect('expenses')


# generate a summary of expenses categorized by their categories over the last six months for visualising that data
def expense_category_summary(request):

    # retrieves the expenses for the current user within the date range of the last six months
    todays_date = datetime.date.today()
    six_months_ago = todays_date-datetime.timedelta(days=30*6)
    expenses = Expense.objects.filter(owner=request.user, date__gte=six_months_ago, date__lte=todays_date)

    # initializes an empty dictionary finalrep that will store the final expense category summary
    finalrep = {}

    # defines a function get_category to extract the category from an expense
    def get_category(expense):
        return expense.category
    
    # creates a unique list of categories using set and map, and converts it to a list category_list
    category_list = list(set(map(get_category, expenses)))

    # defines a function get_expense_category_amount to calculate the total amount spent on a specific category
    # filters expenses by category and sums up their amounts
    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = expenses.filter(category=category)
        for item in filtered_by_category:
            amount += item.amount
        return amount
    
    # Iterates over each expense and each category. For each category, it calculates the total amount spent on that category 
    # and stores it in the finalrep dictionary
    for x in expenses:
        for y in category_list:
            finalrep[y] = get_expense_category_amount(y)

    # returns a JSON response containing the expense category summary in the format {'expense_category_data': finalrep}, 
    # taken as input by the frontend
    return JsonResponse({'expense_category_data': finalrep}, safe=False)

# renders a template named 'expenses/stats.html' to show thw visaulisation
def stats_view(request):
    return render(request, 'expenses/stats.html')

# generates a CSV file containing information about expenses and returns it as a downloadable file
def export_csv(request):

    # creates an HttpResponse object with the content type set to 'text/csv' to indicate that the response will contain CSV data
    response = HttpResponse(content_type = 'text/csv')

    # sets the Content-Disposition header to specify the filename of the downloadable file
    response['Content-Disposition'] = 'attachment; filename=Expenses' + str(datetime.datetime.now()) + '.csv'

    # creates a csv.writer object associated with the response and writes the header row to the CSV file
    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Category', 'Date'])

    # retrieves expenses filtered by the current user
    expenses = Expense.objects.filter(owner = request.user)

    # iterates through the expenses and writes each expense's amount, description, category, and date to the CSV file
    for expense in expenses:
        writer.writerow([expense.amount, expense.description, expense.category, expense.date])
    
    # it returns the response, which contains the generated CSV data. 
    # The user's browser will prompt the user to download the file with the specified filename
    return response


# generates an Excel (xls) file
def export_excel(request):

    # creates an HttpResponse object with the content type set to 'application/ms-excel' to indicate that the response will contain Excel data
    response = HttpResponse(content_type = 'application/ms-excel')

    # sets the Content-Disposition header to specify the filename of the downloadable file
    response['Content-Disposition'] = 'attachment; filename=Expenses' + str(datetime.datetime.now()) + '.xls'

    # creates an Excel workbook (xlwt.Workbook), adds a sheet named 'Expenses' (wb.add_sheet), 
    # and initializes variables for row number and font style
    wb = xlwt.Workbook(encoding = 'utf-8')
    ws = wb.add_sheet('Expenses')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    # defines the column headers and writes them to the Excel file
    columns = [['Amount', 'Description', 'Category', 'Date']]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()

    # retrieves expense data for the current user and writes each row of data to the Excel file
    rows = Expense.objects.filter(owner = request.user).values_list('amount', 'description', 'category', 'date')

    for row in rows:
        row_num += 1

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)

    # saves the workbook to the response, making it available for download, and returns the response
    wb.save(response)

    return response

#  generates a PDF file containing information about expenses and returns it as an inline downloadable file
def export_pdf(request):

    # creates an HttpResponse object with the content type set to 'application/pdf' to indicate that the response will contain PDF data
    response = HttpResponse(content_type = 'application/pdf')

    # sets the Content-Disposition header to specify the filename of the downloadable file
    response['Content-Disposition'] = 'inline; attachment; filename=Expenses' + str(datetime.datetime.now()) + '.pdf'
    response['Content-Transfer-Encoding'] = 'binary'

    # retrieves expenses and calculates the sum of the 'amount' field
    expenses = Expense.objects.filter(owner = request.user)
    sum = expenses.aggregate(Sum('amount'))

    # renders an HTML template (pdf-output.html) with expense data and the total amount 
    # The HTML is then converted to a PDF using the write_pdf method of the HTML class.
    html_string = render_to_string('expenses/pdf-output.html',{'expenses': expenses, 'total': sum['amount__sum']})
    html = HTML(string = html_string)
    result = html.write_pdf()

    # writes the PDF content to a temporary file and then writes the content of the file to the response
    with tempfile.NamedTemporaryFile(delete = True) as output:
        output.write(result)
        output.flush()
        output.seek(0)
       
        response.write(output.read())
    # it returns the response, which contains the generated PDF data 
    # The user's browser will prompt the user to download the file with the specified filename
    return response

from django.http import HttpResponseNotAllowed

from django.http import JsonResponse
from django.utils import translation

 
@login_required
def change_language(request):
    language = request.POST.get('language', request.GET.get('language', ''))
    
    print(f'Received language: {language}')  # for debugging
    response_data = {}

    if language == 'sw' or language == 'en':
        request.session['django_language'] = language
        response_data = {
            'status': 'success',
            'message': 'Language changed successfully'
        }
        translation.activate(language)
        print(f'Current language: {translation.get_language()}')  # for debugging
    else:
        response_data = {
            'status': 'error',
            'message': 'Invalid language'
        }
        print(f'Invalid language: {language}')  # for debugging

    return render(request, "expenses/index.html")




from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from notifications_app.models import BroadcastNotification
def home(request):
    
    return render(request, 'expenses/index.html',{
        'room_name': "broadcast"
    })

def test(request):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
         "notification_broadcast",
        {
            'type': 'send_notification',
            'message': json.dumps("Notification")
        }
    )
    return HttpResponse("Done")

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def mark_notification_as_read(request, notification_id):
    print('Marking notification as read. ID:', notification_id)
    
    notification = get_object_or_404(BroadcastNotification, pk=notification_id)
    notification.is_read = True
    notification.save()
    
    print('Notification marked as read. ID:', notification_id)
    return JsonResponse({'success': True, 'notification_already_read': notification.is_read})

#dashboard implementation
def dashboard(request):
    
    total_user_expenses = Expense.objects.filter(owner=request.user).aggregate(Sum('amount'))['amount__sum']
    user_budget = UserPreference.objects.get(user=request.user).budget
    
    if total_user_expenses is None:
        total_user_expenses = Decimal('0.0')

    difference = user_budget - Decimal(str(total_user_expenses))

    currency = UserPreference.objects.filter(user=request.user).first()
    if currency:
        currency = currency.currency
    context = {
        'total_user_expenses': total_user_expenses,
        'user_budget': user_budget,
        'currency': currency,
        'difference': difference
    }

    return render(request, 'dashboard.html', context)

#dashboard graph
def dashboard_json(request):
    total_user_expenses = Expense.objects.filter(owner=request.user).aggregate(Sum('amount'))['amount__sum']
    user_budget = UserPreference.objects.get(user=request.user).budget
    
    if total_user_expenses is None:
        total_user_expenses = Decimal('0.0')

    difference = user_budget - Decimal(str(total_user_expenses))

    data = {
        'total_user_expenses': str(total_user_expenses),
        'user_budget': str(user_budget),
        'difference': str(difference)
    }

    return JsonResponse(data)