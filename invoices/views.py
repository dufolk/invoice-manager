from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import Invoice, ExpenseType, TravelInvoice
import json
from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from collections import defaultdict

def dashboard(request):
    # 基础统计数据
    total_amount = Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0
    invoice_count = Invoice.objects.count()
    daily_count = Invoice.objects.filter(invoice_type='DAILY').count()
    travel_count = Invoice.objects.filter(invoice_type='TRAVEL').count()

    # 获取最近12个月的数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # 月度趋势数据
    monthly_data = (Invoice.objects
                   .filter(invoice_date__range=[start_date, end_date])
                   .annotate(month=TruncMonth('invoice_date'))
                   .values('month')
                   .annotate(total=Sum('amount'))
                   .order_by('month'))
    
    monthly_labels = [item['month'].strftime('%Y-%m') for item in monthly_data]
    monthly_values = [float(item['total']) for item in monthly_data]

    # 发票类型占比
    type_data = [
        {'name': '日常发票', 'value': daily_count},
        {'name': '差旅发票', 'value': travel_count}
    ]

    # 费用类型分布
    expense_types = (Invoice.objects
                    .values('expense_type__name')
                    .annotate(count=Count('id'))
                    .order_by('-count'))
    
    expense_type_data = [
        {'name': item['expense_type__name'], 'value': item['count']}
        for item in expense_types
    ]

    # 差旅费用构成
    travel_categories = (TravelInvoice.objects
                        .values('expense_category')
                        .annotate(total=Sum('invoice__amount')))
    
    travel_labels = [item['expense_category'] for item in travel_categories]
    travel_values = [float(item['total']) for item in travel_categories]

    context = {
        'total_amount': "{:,.2f}".format(total_amount),
        'invoice_count': invoice_count,
        'daily_count': daily_count,
        'travel_count': travel_count,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_values),
        'type_data': json.dumps(type_data),
        'expense_type_data': json.dumps(expense_type_data),
        'travel_labels': json.dumps(travel_labels),
        'travel_data': json.dumps(travel_values)
    }

    return render(request, 'invoices/dashboard.html', context)

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, 'invoices/admin/login.html', {
                'error_message': '用户名或密码错误'
            })
    
    return render(request, 'invoices/admin/login.html')

@login_required
def admin_dashboard(request):
    return render(request, 'invoices/admin/dashboard.html')

def admin_logout(request):
    logout(request)
    return redirect('dashboard')

def manage_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            # 如果用户没有设置全名，则使用用户名
            if not user.get_full_name():
                # 这里可以添加默认的昵称映射
                nickname_map = {
                    'hyouyu': '于沆佑',
                    # 可以添加更多映射
                }
                if user.username in nickname_map:
                    user.first_name = nickname_map[user.username]
                    user.save()
            return redirect('invoices:manage_dashboard')
        else:
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'invoices/manage/login.html')

@login_required
def manage_logout(request):
    logout(request)
    return redirect('invoices:dashboard')

@login_required
def manage_dashboard(request):
    context = {
        'invoice_count': Invoice.objects.count(),
        'total_amount': Invoice.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'expense_type_count': ExpenseType.objects.count(),
        'recent_invoices': Invoice.objects.all().order_by('-invoice_date')[:5],  # 最近5条记录
    }
    return render(request, 'invoices/manage/dashboard.html', context)

@login_required
def manage_invoice_list(request):
    # 获取查询参数
    search_query = request.GET.get('search', '')
    invoice_type = request.GET.get('type', '')
    expense_type_id = request.GET.get('expense_type', '')
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')

    # 构建查询
    invoices = Invoice.objects.all()
    
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(reimbursement_person__icontains=search_query)
        )
    
    if invoice_type:
        invoices = invoices.filter(invoice_type=invoice_type)
    
    if expense_type_id:
        invoices = invoices.filter(expense_type_id=expense_type_id)
        
    if year:
        invoices = invoices.filter(invoice_date__year=int(year))
        
    if month:
        invoices = invoices.filter(invoice_date__month=int(month))

    # 计算筛选结果的总金额
    total_amount = invoices.aggregate(Sum('amount'))['amount__sum'] or 0

    # 获取可用的年份列表
    available_years = (Invoice.objects
                      .dates('invoice_date', 'year', order='DESC')
                      .values_list('invoice_date__year', flat=True)
                      .distinct())

    # 排序
    invoices = invoices.order_by('-invoice_date')

    # 分页
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'invoices': page_obj,
        'expense_types': ExpenseType.objects.all(),
        'available_years': available_years,
        'available_months': range(1, 13),
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'total_amount': total_amount,  # 添加总金额到上下文
    }
    
    return render(request, 'invoices/manage/invoice_list.html', context)

@login_required
def manage_invoice_add(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 创建发票
                invoice = Invoice.objects.create(
                    invoice_number=request.POST['invoice_number'],
                    invoice_type=request.POST['invoice_type'],
                    amount=request.POST['amount'],
                    details=request.POST.get('details', ''),
                    invoice_date=request.POST['invoice_date'],
                    image=request.FILES['image'],
                    expense_type_id=request.POST['expense_type'],
                    reimbursement_person=request.POST['reimbursement_person']
                )

                # 如果是差旅发票，创建关联的差旅信息
                if invoice.invoice_type == 'TRAVEL':
                    TravelInvoice.objects.create(
                        invoice=invoice,
                        traveler=request.POST['traveler'],
                        start_date=request.POST['start_date'],
                        end_date=request.POST['end_date'],
                        destination=request.POST['destination'],
                        expense_category=request.POST['expense_category']
                    )

            messages.success(request, '发票添加成功')
            return redirect('invoices:manage_invoice_list')
        except Exception as e:
            messages.error(request, f'发票添加失败：{str(e)}')
            
    context = {
        'expense_types': ExpenseType.objects.all()
    }
    return render(request, 'invoices/manage/invoice_form.html', context)

@login_required
def manage_invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 更新发票信息
                invoice.invoice_number = request.POST['invoice_number']
                invoice.invoice_type = request.POST['invoice_type']
                invoice.amount = request.POST['amount']
                invoice.details = request.POST.get('details', '')
                invoice.invoice_date = request.POST['invoice_date']
                invoice.expense_type_id = request.POST['expense_type']
                invoice.reimbursement_person = request.POST['reimbursement_person']
                
                if 'image' in request.FILES:
                    invoice.image = request.FILES['image']
                
                invoice.save()

                # 处理差旅信息
                if invoice.invoice_type == 'TRAVEL':
                    travel_invoice, created = TravelInvoice.objects.get_or_create(invoice=invoice)
                    travel_invoice.traveler = request.POST['traveler']
                    travel_invoice.start_date = request.POST['start_date']
                    travel_invoice.end_date = request.POST['end_date']
                    travel_invoice.destination = request.POST['destination']
                    travel_invoice.expense_category = request.POST['expense_category']
                    travel_invoice.save()
                else:
                    TravelInvoice.objects.filter(invoice=invoice).delete()

            messages.success(request, '发票更新成功')
            return redirect('invoices:manage_invoice_list')
        except Exception as e:
            messages.error(request, f'发票更新失败：{str(e)}')
    
    context = {
        'invoice': invoice,
        'expense_types': ExpenseType.objects.all()
    }
    return render(request, 'invoices/manage/invoice_form.html', context)

@login_required
def manage_invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, '发票已删除')
        return redirect('invoices:manage_invoice_list')
    return render(request, 'invoices/manage/invoice_confirm_delete.html', {'invoice': invoice})

@login_required
def manage_expense_type_list(request):
    expense_types = ExpenseType.objects.all()
    return render(request, 'invoices/manage/expense_type_list.html', {'expense_types': expense_types})

@login_required
def manage_expense_type_add(request):
    if request.method == 'POST':
        try:
            ExpenseType.objects.create(
                name=request.POST['name'],
                description=request.POST.get('description', '')
            )
            messages.success(request, '费用类型添加成功')
            return redirect('invoices:manage_expense_type_list')
        except Exception as e:
            messages.error(request, f'费用类型添加失败：{str(e)}')
    
    return render(request, 'invoices/manage/expense_type_form.html')

@login_required
def manage_expense_type_edit(request, pk):
    expense_type = get_object_or_404(ExpenseType, pk=pk)
    
    if request.method == 'POST':
        try:
            expense_type.name = request.POST['name']
            expense_type.description = request.POST.get('description', '')
            expense_type.save()
            messages.success(request, '费用类型更新成功')
            return redirect('invoices:manage_expense_type_list')
        except Exception as e:
            messages.error(request, f'费用类型更新失败：{str(e)}')
    
    return render(request, 'invoices/manage/expense_type_form.html', {'expense_type': expense_type})

@login_required
def manage_expense_type_delete(request, pk):
    expense_type = get_object_or_404(ExpenseType, pk=pk)
    if request.method == 'POST':
        expense_type.delete()
        messages.success(request, '费用类型已删除')
        return redirect('invoices:manage_expense_type_list')
    return render(request, 'invoices/manage/expense_type_confirm_delete.html', {'expense_type': expense_type})

@login_required
def manage_personal_stats(request):
    # 获取搜索参数
    search_query = request.GET.get('search', '')
    
    # 获取最近12个月的数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # 按人员和月份统计，只获取有数据的月份
    stats = (Invoice.objects
            .filter(invoice_date__range=[start_date, end_date])
            .filter(reimbursement_person__icontains=search_query)
            .annotate(month=TruncMonth('invoice_date'))
            .values('month', 'reimbursement_person')
            .annotate(total=Sum('amount'))
            .order_by('month', 'reimbursement_person'))
    
    # 整理数据
    person_data = defaultdict(dict)
    months = []
    
    # 收集有数据的月份和对应的金额
    for item in stats:
        month = item['month'].strftime('%Y-%m')
        person = item['reimbursement_person']
        amount = float(item['total'])
        
        if month not in months:
            months.append(month)
        person_data[person][month] = amount
    
    # 构建系列数据
    series = []
    colors = ['#00C6FF', '#0088FF', '#7EAEFF', '#4CAF50', '#FF4444']
    
    for i, (person, month_data) in enumerate(person_data.items()):
        # 只使用有数据的点
        data = []
        for month in months:
            if month in month_data:
                data.append([month, month_data[month]])
        
        series.append({
            'name': person,
            'type': 'line',
            'data': data,
            'smooth': True,
            'symbol': 'circle',
            'symbolSize': 8,
            'lineStyle': {
                'width': 3,
                'color': colors[i % len(colors)]
            },
            'itemStyle': {
                'color': colors[i % len(colors)]
            }
        })
    
    return JsonResponse({
        'months': months,
        'series': series
    })

@login_required
def manage_expense_type_stats(request):
    # 获取费用类型统计
    stats = (Invoice.objects
            .values('expense_type__name')
            .annotate(value=Sum('amount'))
            .order_by('-value'))
    
    data = [{
        'name': item['expense_type__name'],
        'value': float(item['value'])
    } for item in stats]
    
    return JsonResponse(data, safe=False)

@login_required
def manage_invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    data = {
        'invoice_number': invoice.invoice_number,
        'invoice_type_display': invoice.get_invoice_type_display(),
        'expense_type': invoice.expense_type.name,
        'amount': float(invoice.amount),
        'reimbursement_person': invoice.reimbursement_person,
        'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d'),
        'details': invoice.details,
        'remarks': invoice.remarks,
        'image_url': invoice.image.url if invoice.image else '',
    }
    return JsonResponse(data)
