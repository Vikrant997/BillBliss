from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('', views.index, name = "expenses"),
    path('add-expense', views.add_expense, name = "add-expenses"),
    path('edit-expense/<int:id>', views.expense_edit, name = "expense-edit"),
    path('expense-delete/<int:id>', views.delete_expense, name = "expense-delete"),
    path('search-expenses', csrf_exempt(views.search_expenses), name = "search_expenses"),
    path('expense_category_summary', csrf_exempt(views.expense_category_summary), name = "expense_category_summary"),
    path('stats', csrf_exempt(views.stats_view), name = "stats"),
    path('export_csv', csrf_exempt(views.export_csv), name = "export-csv"),
    path('export_excel', csrf_exempt(views.export_excel), name = "export-excel"),
    path('export_pdf', csrf_exempt(views.export_pdf), name = "export-pdf"),
    path('other_page', views.index, name = "other_page"),
    path('check_budget_status/', views.check_budget_status, name='check_budget_status'),
]