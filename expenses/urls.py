from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls.i18n import i18n_patterns

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

    path('change-language/', views.change_language, name='change_language'),
    path('index/', views.index, name='index'),
    path('test/', views.test, name = 'home'),
    path('', views.home, name = 'home'),

    path('mark_notification_as_read/<int:notification_id>/',views.mark_notification_as_read, name='mark_notification_as_read'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-json/', views.dashboard_json, name='dashboard_json'), 

]