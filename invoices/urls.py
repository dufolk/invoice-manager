from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # 管理功能的URL
    path('manage/', views.manage_dashboard, name='manage_dashboard'),
    path('manage/login/', views.manage_login, name='manage_login'),
    path('manage/logout/', views.manage_logout, name='manage_logout'),
    path('manage/invoices/', views.manage_invoice_list, name='manage_invoice_list'),
    path('manage/invoices/add/', views.manage_invoice_add, name='manage_invoice_add'),
    path('manage/invoices/<int:pk>/edit/', views.manage_invoice_edit, name='manage_invoice_edit'),
    path('manage/invoices/<int:pk>/delete/', views.manage_invoice_delete, name='manage_invoice_delete'),
    path('manage/expense-types/', views.manage_expense_type_list, name='manage_expense_type_list'),
    path('manage/expense-types/add/', views.manage_expense_type_add, name='manage_expense_type_add'),
    path('manage/expense-types/<int:pk>/edit/', views.manage_expense_type_edit, name='manage_expense_type_edit'),
    path('manage/expense-types/<int:pk>/delete/', views.manage_expense_type_delete, name='manage_expense_type_delete'),
    path('manage/stats/personal/', views.manage_personal_stats, name='manage_personal_stats'),
    path('manage/stats/expense-type/', views.manage_expense_type_stats, name='manage_expense_type_stats'),
    path('manage/invoice/<int:pk>/detail/', views.manage_invoice_detail, name='manage_invoice_detail'),
    path('manage/invoices/batch-delete/', views.manage_invoice_batch_delete, name='manage_invoice_batch_delete'),
    path('manage/parse-invoice/', views.parse_invoice, name='parse_invoice'),
    path('manage/reimbursement/', views.manage_reimbursement_list, 
         name='manage_reimbursement_list'),
    path('manage/fund/', views.manage_fund_list, name='manage_fund_list'),
] 