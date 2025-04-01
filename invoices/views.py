from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import Invoice, ExpenseType, TravelInvoice, ReimbursementRecord, FundRecord, TransportDetail, AccommodationDetail
import json
from datetime import datetime, timedelta, timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from collections import defaultdict
import tempfile
from scripts.invoice_parser import get_invoice_info
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

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

@ensure_csrf_cookie
def manage_login(request):
    # 如果用户已登录，直接重定向到管理面板
    if request.user.is_authenticated:
        return redirect('invoices:manage_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'欢迎回来，{user.get_full_name() or user.username}')
            return redirect('invoices:manage_dashboard')
        else:
            messages.error(request, '用户名或密码错误')
            return render(request, 'invoices/manage/login.html')
    
    return render(request, 'invoices/manage/login.html')

@login_required
def manage_logout(request):
    logout(request)
    return redirect('invoices:dashboard')

@login_required
def manage_dashboard(request):
    if request.user.is_staff:
        # 管理员看到所有数据
        context = {
            'invoice_count': Invoice.objects.count(),
            'total_amount': Invoice.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
            'expense_type_count': ExpenseType.objects.count(),
            'recent_invoices': Invoice.objects.all().order_by('-invoice_date')[:5],
        }
    else:
        # 普通用户只看到自己的数据
        user_invoices = Invoice.objects.filter(reimbursement_person=request.user.get_full_name())
        context = {
            'invoice_count': user_invoices.count(),
            'total_amount': user_invoices.aggregate(Sum('amount'))['amount__sum'] or 0,
            'recent_invoices': user_invoices.order_by('-invoice_date')[:5],
        }
    
    # 添加用户类型到上下文
    context['is_staff'] = request.user.is_staff
    return render(request, 'invoices/manage/dashboard.html', context)

@login_required
def manage_invoice_list(request):
    # 获取查询参数，只用于初始化筛选条件
    search_query = request.GET.get('search', '')
    invoice_type = request.GET.get('type', '')
    expense_type_id = request.GET.get('expense_type', '')
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')

    # 获取可用的年份列表
    available_years = (Invoice.objects
                      .dates('invoice_date', 'year', order='DESC')
                      .values_list('invoice_date__year', flat=True)
                      .distinct())

    context = {
        'expense_types': ExpenseType.objects.all(),
        'available_years': available_years,
        'available_months': range(1, 13),
        'is_staff': request.user.is_staff,
        # 移除了 invoices, total_amount, current_sort, current_order 等
        # 因为这些数据现在由 AJAX 请求获取
    }
    
    return render(request, 'invoices/manage/invoice_list.html', context)

@login_required
def manage_invoice_add(request):
    if request.method == 'POST':
        try:
            # 检查发票号是否已存在
            invoice_number = request.POST['invoice_number']
            if Invoice.objects.filter(invoice_number=invoice_number).exists():
                return JsonResponse({
                    'success': False,
                    'error': f'发票号 {invoice_number} 已存在'
                })

            with transaction.atomic():
                # 创建发票基本信息
                invoice_data = {
                    'invoice_number': invoice_number,
                    'invoice_type': request.POST['invoice_type'],
                    'amount': float(request.POST['amount']),
                    'details': request.POST.get('details', ''),
                    'remarks': request.POST.get('remarks', ''),
                    'invoice_date': request.POST['invoice_date'],
                    'expense_type_id': request.POST['expense_type'],
                    'reimbursement_person': request.POST['reimbursement_person']
                }
                
                # 如果是管理员，添加报销状态相关字段
                if request.user.is_staff:
                    invoice_data.update({
                        'reimbursement_status': request.POST.get('reimbursement_status', 'NOT_SUBMITTED'),
                        'status_remarks': request.POST.get('status_remarks', '')
                    })
                
                invoice = Invoice.objects.create(**invoice_data)
                
                # 处理发票文件上传
                if 'file' in request.FILES:
                    invoice.file = request.FILES['file']
                
                # 处理附件上传
                if 'attachment' in request.FILES:
                    invoice.attachment = request.FILES['attachment']
                
                # 检查是否可能存在问题
                invoice.check_potential_issues()
                invoice.save()
                
                # 如果是差旅发票，创建关联的差旅信息
                if invoice.invoice_type == 'TRAVEL':
                    travel_invoice = TravelInvoice.objects.create(
                        invoice=invoice,
                        traveler=request.POST['traveler'],
                        start_date=request.POST['start_date'],
                        end_date=request.POST['end_date'],
                        destination=request.POST['destination'],
                        expense_category=request.POST.get('expense_category', '')
                    )
                    
                    # 根据费用类型创建相应的明细
                    expense_type_name = invoice.expense_type.name
                    if expense_type_name == '交通费':
                        TransportDetail.objects.create(
                            travel_invoice=travel_invoice,
                            transport_type=request.POST['transport_type'],
                            departure_time=request.POST['departure_date'],
                            departure_place=request.POST['departure_place'],
                            destination=request.POST['destination'],
                            seat_type=request.POST['seat_type']
                        )
                    elif expense_type_name == '住宿费':
                        AccommodationDetail.objects.create(
                            travel_invoice=travel_invoice,
                            check_in_date=request.POST['check_in_date'],
                            check_out_date=request.POST['check_out_date'],
                            hotel_name=request.POST['hotel_name']
                        )
                    
                    # 重新检查问题（因为现在有了差旅信息）
                    invoice.check_potential_issues()
                    invoice.save()

            # 返回 JSON 响应
            return JsonResponse({
                'success': True,
                'message': '发票添加成功！',
                'redirect_url': reverse('invoices:manage_invoice_list')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return render(request, 'invoices/manage/invoice_form.html', {'expense_types': ExpenseType.objects.all(), 'invoice_type': 'DAILY'})

@login_required
def manage_invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 更新基本信息
                invoice.invoice_number = request.POST['invoice_number']
                invoice.invoice_type = request.POST['invoice_type']
                invoice.amount = float(request.POST['amount'])
                invoice.details = request.POST.get('details', '')
                invoice.remarks = request.POST.get('remarks', '')
                invoice.invoice_date = request.POST['invoice_date']
                invoice.expense_type_id = request.POST['expense_type']
                invoice.reimbursement_person = request.POST['reimbursement_person']
                
                # 如果是管理员，更新报销状态相关字段
                if request.user.is_staff:
                    invoice.reimbursement_status = request.POST.get('reimbursement_status', 'NOT_SUBMITTED')
                    invoice.status_remarks = request.POST.get('status_remarks', '')
                
                # 处理发票文件上传
                if 'file' in request.FILES:
                    invoice.file = request.FILES['file']
                
                # 处理附件上传
                if 'attachment' in request.FILES:
                    invoice.attachment = request.FILES['attachment']
                
                # 检查是否可能存在问题
                invoice.check_potential_issues()
                invoice.save()
                
                # 如果是差旅发票，更新或创建差旅信息
                if invoice.invoice_type == 'TRAVEL':
                    travel_data = {
                        'traveler': request.POST['traveler'],
                        'start_date': request.POST['start_date'],
                        'end_date': request.POST['end_date'],
                        'destination': request.POST['destination'],
                        'expense_category': request.POST.get('expense_category', '')
                    }
                    
                    travel_invoice, created = TravelInvoice.objects.get_or_create(
                        invoice=invoice,
                        defaults=travel_data
                    )
                    
                    if not created:
                        for key, value in travel_data.items():
                            setattr(travel_invoice, key, value)
                        travel_invoice.save()
                    
                    # 根据费用类型更新或创建相应的明细
                    expense_type_name = invoice.expense_type.name
                    if expense_type_name == '交通费':
                        # 删除旧的交通明细
                        TransportDetail.objects.filter(travel_invoice=travel_invoice).delete()
                        # 创建新的交通明细
                        TransportDetail.objects.create(
                            travel_invoice=travel_invoice,
                            transport_type=request.POST['transport_type'],
                            departure_time=request.POST['departure_date'],
                            departure_place=request.POST['departure_place'],
                            destination=request.POST['destination'],
                            seat_type=request.POST['seat_type']
                        )
                    elif expense_type_name == '住宿费':
                        # 删除旧的住宿明细
                        AccommodationDetail.objects.filter(travel_invoice=travel_invoice).delete()
                        # 创建新的住宿明细
                        AccommodationDetail.objects.create(
                            travel_invoice=travel_invoice,
                            check_in_date=request.POST['check_in_date'],
                            check_out_date=request.POST['check_out_date'],
                            hotel_name=request.POST['hotel_name']
                        )
                    
                    # 重新检查问题（因为差旅信息可能已更新）
                    invoice.check_potential_issues()
                    invoice.save()
                
            return JsonResponse({
                'success': True,
                'message': '发票更新成功！',
                'redirect_url': reverse('invoices:manage_invoice_list')
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    context = {
        'invoice': invoice,
        'expense_types': ExpenseType.objects.all(),
        'invoice_type': invoice.invoice_type
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
                category=request.POST['category'],
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
            expense_type.category = request.POST['category']
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
        'invoice_type': invoice.invoice_type,
        'invoice_type_display': invoice.get_invoice_type_display(),
        'expense_type': invoice.expense_type.name,
        'amount': float(invoice.amount),
        'invoice_date': invoice.invoice_date,
        'reimbursement_person': invoice.reimbursement_person,
        'details': invoice.details,
        'remarks': invoice.remarks,
        'file_url': invoice.file.url if invoice.file else '',
        'attachment_url': invoice.attachment.url if invoice.attachment else '',
        'attachment_name': invoice.attachment.name.split('/')[-1] if invoice.attachment else '',
        'has_potential_issue': invoice.has_potential_issue,
    }
    return JsonResponse(data)

@login_required
def manage_invoice_batch_delete(request):
    if request.method == 'POST':
        # 获取请求体中的发票 ID 列表
        try:
            data = json.loads(request.body)
            invoice_ids = data.get('invoice_ids', [])
            
            if invoice_ids:
                # 批量删除发票
                Invoice.objects.filter(id__in=invoice_ids).delete()
                return JsonResponse({'success': True, 'message': f'成功删除 {len(invoice_ids)} 张发票'})
            else:
                return JsonResponse({'success': False, 'error': '未提供发票 ID'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': '不支持的请求方法'})

@login_required
def parse_invoice(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '仅支持POST请求'})
    
    try:
        base64_data = request.POST.get('file_data')
        file_type = request.POST.get('file_type')
        
        if not base64_data or not file_type:
            return JsonResponse({'success': False, 'error': '未收到完整的文件数据'})
        
        # 调用解析函数
        result = get_invoice_info(base64_data, file_type)
        parsed_data = json.loads(result)
        
        if 'words_result' in parsed_data:
            return JsonResponse({
                'success': True,
                'words_result': parsed_data['words_result']
            })
        else:
            return JsonResponse({
                'success': False,
                'error_msg': parsed_data.get('error_msg', '未知错误')
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error_msg': str(e)
        })

@login_required
def manage_invoice_create(request):
    if request.method == 'POST':
        try:
            # 获取基本发票信息
            invoice_data = {
                'invoice_number': request.POST.get('invoice_number'),
                'invoice_type': request.POST.get('invoice_type'),
                'expense_type_id': request.POST.get('expense_type'),
                'amount': request.POST.get('amount'),
                'invoice_date': request.POST.get('invoice_date'),
                'reimbursement_person': request.POST.get('reimbursement_person'),
                'details': request.POST.get('details'),
                'remarks': request.POST.get('remarks'),
            }
            
            # 创建发票记录
            invoice = Invoice.objects.create(**invoice_data)
            
            # 处理上传的图片
            if 'file' in request.FILES:
                invoice.file = request.FILES['file']
                invoice.save()
            
            # 如果是差旅发票，创建关联的差旅信息
            if invoice.invoice_type == 'TRAVEL':
                travel_data = {
                    'invoice': invoice,
                    'traveler': request.POST.get('traveler'),
                    'start_date': request.POST.get('start_date'),
                    'end_date': request.POST.get('end_date'),
                    'destination': request.POST.get('destination'),
                }
                TravelInvoice.objects.create(**travel_data)
            
            messages.success(request, '发票添加成功！')
            return JsonResponse({'success': True, 'message': '发票添加成功！'})
            
        except Exception as e:
            messages.error(request, f'发票添加失败：{str(e)}')
            return JsonResponse({'success': False, 'error': str(e)})
    
    # ... 其余代码保持不变 ...

@login_required
def manage_reimbursement_list(request):
    # 获取筛选参数
    record_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    # 构建查询
    records = ReimbursementRecord.objects.all()
    
    if record_type:
        records = records.filter(record_type=record_type)
    if status:
        records = records.filter(status=status)
        
    # 按时间倒序排序
    records = records.order_by('-reimbursement_date')
    
    context = {
        'records': records
    }
    
    return render(request, 'invoices/manage/reimbursement_list.html', context)

@login_required
def manage_fund_list(request):
    # 获取查询参数
    search_query = request.GET.get('search', '')
    record_type = request.GET.get('type', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # 构建查询
    records = FundRecord.objects.all()
    
    if search_query:
        records = records.filter(description__icontains=search_query)
    
    if record_type:
        records = records.filter(record_type=record_type)
        
    if start_date:
        records = records.filter(record_date__gte=start_date)
        
    if end_date:
        records = records.filter(record_date__lte=end_date)
    
    # 按时间倒序排序
    records = records.order_by('-record_date', '-created_at')
    
    # 获取最新余额
    latest_record = FundRecord.objects.order_by('-record_date', '-created_at').first()
    current_balance = latest_record.balance if latest_record else 0
    
    # 分页
    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'records': page_obj,
        'current_balance': current_balance,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'invoices/manage/fund_list.html', context)

@login_required
def manage_fund_add(request):
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            record_type = request.POST.get('record_type')
            
            # 如果是支出，将金额转为负数
            if record_type == 'EXPENSE':
                amount = -abs(amount)
            else:
                amount = abs(amount)
                
            record = FundRecord.objects.create(
                amount=amount,
                record_type=record_type,
                description=request.POST.get('description', ''),
                record_date=request.POST.get('record_date')
            )
            
            messages.success(request, '经费记录添加成功')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': '不支持的请求方法'})

@login_required
def manage_fund_edit(request, pk):
    record = get_object_or_404(FundRecord, pk=pk)
    
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            record_type = request.POST.get('record_type')
            
            # 如果是支出，将金额转为负数
            if record_type == 'EXPENSE':
                amount = -abs(amount)
            else:
                amount = abs(amount)
                
            record.amount = amount
            record.record_type = record_type
            record.description = request.POST.get('description', '')
            record.record_date = request.POST.get('record_date')
            record.save()
            
            messages.success(request, '经费记录更新成功')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    data = {
        'id': record.id,
        'amount': abs(float(record.amount)),
        'record_type': record.record_type,
        'description': record.description,
        'record_date': record.record_date.isoformat()
    }
    return JsonResponse(data)

@login_required
def manage_fund_delete(request, pk):
    if request.method == 'POST':
        record = get_object_or_404(FundRecord, pk=pk)
        record.delete()
        messages.success(request, '经费记录已删除')
        return redirect('invoices:manage_fund_list')
    return JsonResponse({'success': False, 'error': '不支持的请求方法'})

@login_required
def manage_reimbursement_add(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                record = ReimbursementRecord.objects.create(
                    reimbursement_date=timezone.now().date(),
                    record_type=request.POST['record_type'],
                    remarks=request.POST.get('remarks', '')
                )
                
                # 添加关联的发票
                invoice_ids = request.POST.getlist('invoice_ids[]')
                if invoice_ids:
                    # 计算总金额
                    total = Invoice.objects.filter(id__in=invoice_ids).aggregate(
                        total=Sum('amount'))['total'] or 0
                    record.total_amount = total
                    record.save()
                    
                    record.invoices.set(invoice_ids)
                    # 更新发票的报销日期和状态
                    Invoice.objects.filter(id__in=invoice_ids).update(
                        reimbursement_date=record.reimbursement_date,
                        reimbursement_status='PENDING'  # 更新状态为"未报销"
                    )
                    
                messages.success(request, '报账记录创建成功')
                return redirect('invoices:manage_reimbursement_list')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
            
    return redirect('invoices:manage_reimbursement_list')

@login_required
def manage_reimbursement_complete(request, pk):
    if request.method == 'POST':
        try:
            record = get_object_or_404(ReimbursementRecord, pk=pk)
            record.status = 'COMPLETED'
            # 更新关联发票的状态
            record.invoices.all().update(
                reimbursement_status='TRANSFERRED'
            )
            record.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': '不支持的请求方法'})

@login_required
def manage_unreimbursed_invoices(request):
    # 获取未报账的发票
    invoices = Invoice.objects.filter(
        reimbursementrecord__isnull=True
    ).values(
        'id', 
        'invoice_number', 
        'amount', 
        'reimbursement_person',
        'invoice_date',
        'invoice_type',
        'expense_type__name'
    ).order_by('-invoice_date')  # 按发票日期倒序排序
    
    # 转换为列表并处理数据
    invoice_list = list(invoices)
    for invoice in invoice_list:
        invoice['amount'] = float(invoice['amount'])
        invoice['invoice_date'] = invoice['invoice_date'].strftime('%Y-%m-%d')
        invoice['invoice_type_display'] = dict(Invoice.INVOICE_TYPES).get(invoice['invoice_type'])
        invoice['expense_type_name'] = invoice['expense_type__name']
    
    return JsonResponse({
        'invoices': invoice_list
    })

@login_required
def manage_reimbursement_detail(request, pk):
    record = get_object_or_404(ReimbursementRecord, pk=pk)
    context = {
        'record': record,
        'invoices': record.invoices.all().order_by('-invoice_date')  # 按发票日期倒序排序
    }
    return render(request, 'invoices/manage/reimbursement_detail.html', context)

@login_required
def manage_reimbursement_add_invoice(request, pk):
    if request.method == 'POST':
        try:
            record = get_object_or_404(ReimbursementRecord, pk=pk)
            invoice_ids = request.POST.getlist('invoice_ids[]')
            
            with transaction.atomic():
                # 添加新发票
                record.invoices.add(*invoice_ids)
                # 更新发票的报销日期
                Invoice.objects.filter(id__in=invoice_ids).update(
                    reimbursement_date=record.reimbursement_date,
                    reimbursement_status='PENDING'  # 更新状态为"未报销"
                )
                # 更新总金额
                record.update_total_amount()
                
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET 请求返回可选的发票列表
    invoices = Invoice.objects.filter(
        reimbursementrecord__isnull=True
    ).values('id', 'invoice_number', 'amount', 'reimbursement_person')
    
    return JsonResponse({'invoices': list(invoices)})

@login_required
def manage_reimbursement_remove_invoice(request, pk, invoice_pk):
    if request.method == 'POST':
        try:
            record = get_object_or_404(ReimbursementRecord, pk=pk)
            # 确保发票属于这个报账记录
            if not record.invoices.filter(id=invoice_pk).exists():
                return JsonResponse({
                    'success': False, 
                    'error': '发票不属于此报账记录'
                })
            
            with transaction.atomic():
                # 移除发票关联
                record.invoices.remove(invoice_pk)
                # 清除发票的报销日期
                Invoice.objects.filter(id=invoice_pk).update(
                    reimbursement_date=None
                )
                # 更新总金额
                record.update_total_amount()
                
            return JsonResponse({'success': True})
        except Exception as e:
            import traceback
            print(traceback.format_exc())  # 打印详细错误信息到控制台
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': '不支持的请求方法'})

@login_required
def manage_reimbursement_delete(request, pk):
    record = get_object_or_404(ReimbursementRecord, pk=pk)
    record.delete()
    return redirect('invoices:manage_reimbursement_list')

@login_required
def manage_reimbursement_batch_remove_invoices(request, pk):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            invoice_ids = data.get('invoice_ids', [])
            
            record = get_object_or_404(ReimbursementRecord, pk=pk)
            with transaction.atomic():
                # 批量移除发票关联
                record.invoices.remove(*invoice_ids)
                # 清除发票的报销日期
                Invoice.objects.filter(id__in=invoice_ids).update(
                    reimbursement_date=None
                )
                # 更新总金额
                record.update_total_amount()
                
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': '不支持的请求方法'})

@login_required
def manage_invoice_list_data(request):
    # 获取查询参数
    search_query = request.GET.get('search', '')
    invoice_type = request.GET.get('type', '')
    expense_type_id = request.GET.get('expense_type', '')
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    sort_by = request.GET.get('sort_by', 'invoice_date')
    order = request.GET.get('order', 'desc')
    page = request.GET.get('page', 1)

    # 构建查询
    if request.user.is_staff:
        invoices = Invoice.objects.all()
        if search_query:
            invoices = invoices.filter(
                Q(invoice_number__icontains=search_query) |
                Q(reimbursement_person__icontains=search_query)
            )
    else:
        invoices = Invoice.objects.filter(reimbursement_person=request.user.get_full_name())
        if search_query:
            invoices = invoices.filter(invoice_number__icontains=search_query)

    # 应用其他筛选条件...
    if invoice_type:
        invoices = invoices.filter(invoice_type=invoice_type)
    
    if expense_type_id:
        invoices = invoices.filter(expense_type_id=expense_type_id)
        
    if year:
        invoices = invoices.filter(invoice_date__year=int(year))
        
    if month:
        invoices = invoices.filter(invoice_date__month=int(month))

    # 应用排序
    if order == 'asc':
        invoices = invoices.order_by(sort_by)
    else:
        invoices = invoices.order_by(f'-{sort_by}')

    # 分页
    paginator = Paginator(invoices, 10)
    page_obj = paginator.get_page(page)

    # 构建返回数据
    data = {
        'invoices': [{
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'invoice_type': invoice.get_invoice_type_display(),
            'expense_type': invoice.expense_type.name,
            'amount': float(invoice.amount),
            'reimbursement_person': invoice.reimbursement_person,
            'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d'),
            'has_potential_issue': invoice.has_potential_issue,
            'reimbursement_status': invoice.reimbursement_status,
        } for invoice in page_obj],
        'total_amount': float(invoices.aggregate(Sum('amount'))['amount__sum'] or 0),
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
    }
    
    return JsonResponse(data)

@login_required
def manage_reimbursement_list_data(request):
    # 获取筛选参数
    record_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    sort_by = request.GET.get('sort_by', 'reimbursement_date')
    order = request.GET.get('order', 'desc')
    page = request.GET.get('page', 1)
    
    # 构建查询
    records = ReimbursementRecord.objects.all()
    
    if record_type:
        records = records.filter(record_type=record_type)
    if status:
        records = records.filter(status=status)
        
    # 应用排序
    if order == 'asc':
        records = records.order_by(sort_by)
    else:
        records = records.order_by(f'-{sort_by}')
    
    # 分页
    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(page)
    
    # 构建返回数据
    data = {
        'records': [{
            'id': record.id,
            'reimbursement_date': record.reimbursement_date.strftime('%Y-%m-%d'),
            'record_type': record.get_record_type_display(),
            'invoice_count': record.invoices.count(),
            'total_amount': float(record.total_amount),
            'status': record.get_status_display(),
            'status_code': record.status,
            'remarks': record.remarks or '-'
        } for record in page_obj],
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
    }
    
    return JsonResponse(data)

@login_required
def manage_fund_list_data(request):
    # 获取查询参数
    search_query = request.GET.get('search', '')
    record_type = request.GET.get('type', '')
    date = request.GET.get('date', '')
    sort_by = request.GET.get('sort_by', 'record_date')
    order = request.GET.get('order', 'desc')
    page = request.GET.get('page', 1)
    
    # 构建查询
    records = FundRecord.objects.all()
    
    if search_query:
        records = records.filter(description__icontains=search_query)
    
    if record_type:
        records = records.filter(record_type=record_type)
        
    if date:
        records = records.filter(record_date=date)
    
    # 应用排序
    if sort_by == 'amount':
        # 如果是按金额排序，使用绝对值
        if order == 'asc':
            records = records.extra(
                select={'abs_amount': 'ABS(amount)'}
            ).order_by('abs_amount')
        else:
            records = records.extra(
                select={'abs_amount': 'ABS(amount)'}
            ).order_by('-abs_amount')
    else:
        # 其他字段正常排序
        if order == 'asc':
            records = records.order_by(sort_by)
        else:
            records = records.order_by(f'-{sort_by}')
    
    # 分页
    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(page)
    
    # 获取最新余额
    latest_record = FundRecord.objects.order_by('-record_date', '-created_at').first()
    current_balance = float(latest_record.balance if latest_record else 0)
    
    # 构建返回数据
    data = {
        'records': [{
            'id': record.id,
            'record_date': record.record_date.strftime('%Y-%m-%d'),
            'record_type': record.get_record_type_display(),
            'amount': float(record.amount),
            'balance': float(record.balance),
            'description': record.description
        } for record in page_obj],
        'current_balance': current_balance,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
    }
    
    return JsonResponse(data)
