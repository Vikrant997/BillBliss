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

    # It sets up pagination for the expenses. It uses the Paginator class to paginate the expenses, displaying 5 expenses per page. 
    # The current page number is extracted from the request's GET parameters.
    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)

    # retrieves the user's currency and budget preferences from the UserPreference model
    currency = UserPreference.objects.get(user=request.user).currency
    budget = UserPreference.objects.get(user=request.user).budget

    # creates a context dictionary containing the expenses, the paginated page object, the user's currency preference, and the budget
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency,
        'budget': budget
    }

    # renders the 'expenses/index.html' template with the provided context
    return render(request, 'expenses/index.html', context)


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

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/edit-expense.html', context)
        description = request.POST['description']
        date = request.POST['expense_date']
        category = request.POST['category']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'expenses/edit-expense.html', context)

        # updates the expense object with the new values and saves it to the database
        expense.owner = request.user
        expense.amount = amount
        expense. date = date
        expense.category = category
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

def export_csv(request):
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=Expenses' + str(datetime.datetime.now()) + '.csv'

    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Category', 'Date'])

    expenses = Expense.objects.filter(owner = request.user)

    for expense in expenses:
        writer.writerow([expense.amount, expense.description, expense.category, expense.date])
    
    return response


def export_excel(request):
    response = HttpResponse(content_type = 'application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Expenses' + str(datetime.datetime.now()) + '.xls'

    wb = xlwt.Workbook(encoding = 'utf-8')
    ws = wb.add_sheet('Expenses')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = [['Amount', 'Description', 'Category', 'Date']]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()
    rows = Expense.objects.filter(owner = request.user).values_list('amount', 'description', 'category', 'date')

    for row in rows:
        row_num += 1

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)

    return response


def export_pdf(request):
    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=Expenses' + str(datetime.datetime.now()) + '.pdf'
    response['Content-Transfer-Encoding'] = 'binary'

    expenses = Expense.objects.filter(owner = request.user)
    sum = expenses.aggregate(Sum('amount'))

    html_string = render_to_string('expenses/pdf-output.html',{'expenses': expenses, 'total': sum['amount__sum']})
    html = HTML(string = html_string)
    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete = True) as output:
        output.write(result)
        output.flush()
        output.seek(0)
       
        response.write(output.read())
    
    return response
