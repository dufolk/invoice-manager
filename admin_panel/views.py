from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Sum
from invoices.models import Invoice, ExpenseType, TravelInvoice

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_panel:dashboard')
        else:
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'admin_panel/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('invoices:dashboard')

@login_required
def dashboard(request):
    context = {
        'invoice_count': Invoice.objects.count(),
        'total_amount': Invoice.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'expense_type_count': ExpenseType.objects.count(),
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-invoice_date')
    return render(request, 'admin_panel/invoice_list.html', {'invoices': invoices})

@login_required
def invoice_add(request):
    if request.method == 'POST':
        # 处理表单提交
        pass
    return render(request, 'admin_panel/invoice_form.html')

@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        # 处理表单提交
        pass
    return render(request, 'admin_panel/invoice_form.html', {'invoice': invoice})

@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, '发票已删除')
        return redirect('admin_panel:invoice_list')
    return render(request, 'admin_panel/invoice_confirm_delete.html', {'invoice': invoice})

@login_required
def expense_type_list(request):
    expense_types = ExpenseType.objects.all()
    return render(request, 'admin_panel/expense_type_list.html', {'expense_types': expense_types})

@login_required
def expense_type_add(request):
    if request.method == 'POST':
        # 处理表单提交
        pass
    return render(request, 'admin_panel/expense_type_form.html')

@login_required
def expense_type_edit(request, pk):
    expense_type = get_object_or_404(ExpenseType, pk=pk)
    if request.method == 'POST':
        # 处理表单提交
        pass
    return render(request, 'admin_panel/expense_type_form.html', {'expense_type': expense_type})

@login_required
def expense_type_delete(request, pk):
    expense_type = get_object_or_404(ExpenseType, pk=pk)
    if request.method == 'POST':
        expense_type.delete()
        messages.success(request, '费用类型已删除')
        return redirect('admin_panel:expense_type_list')
    return render(request, 'admin_panel/expense_type_confirm_delete.html', {'expense_type': expense_type})
