from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

class ExpenseType(models.Model):
    """费用类型模型"""
    CATEGORY_CHOICES = [
        ('DAILY', '日常费用'),
        ('TRAVEL', '差旅费用'),
    ]
    
    INITIAL_EXPENSE_TYPES = {
        'DAILY': [
            '书报杂志订阅费',
            '印刷费',
            '邮寄费',
            '仪器设备维修费',
            '会议费',
            '专用材料费',
            '交通费',
            '其他'
        ],
        'TRAVEL': [
            '交通费',
            '住宿费',
            '其他'
        ]
    }
    
    name = models.CharField(max_length=50, verbose_name='类型名称')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='DAILY', 
                              verbose_name='费用分类')

    class Meta:
        verbose_name = '费用类型'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class Invoice(models.Model):
    """发票基础模型"""
    INVOICE_TYPES = [
        ('DAILY', '日常发票'),
        ('TRAVEL', '差旅发票'),
    ]
    
    REIMBURSEMENT_STATUS = [
        ('NOT_SUBMITTED', '未提交'),
        ('PENDING', '未报销'),
        ('NOT_TRANSFERRED', '未转入管理员账户'),
        ('TRANSFERRED', '已转入管理员账户'),
    ]
    
    invoice_number = models.CharField('发票号码', max_length=50, unique=True)
    invoice_type = models.CharField('发票类型', max_length=10, choices=INVOICE_TYPES)
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.PROTECT, verbose_name='费用类型')
    amount = models.DecimalField('金额', max_digits=10, decimal_places=2)
    invoice_date = models.DateField('发票日期')
    reimbursement_date = models.DateField('报销日期', null=True, blank=True)
    reimbursement_person = models.CharField('报销人', max_length=50)
    details = models.TextField('报销内容明细', blank=True)
    remarks = models.TextField('备注', blank=True)
    file = models.FileField(
        '发票文件',
        upload_to='invoices/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        null=True,
        blank=True
    )
    attachment = models.FileField(
        '附件',
        upload_to='attachments/%Y/%m/',
        null=True,
        blank=True,
        help_text='可上传任意类型的附件文件'
    )
    has_potential_issue = models.BooleanField(
        '可能存在问题',
        default=False,
        help_text='日常发票金额超过1000且无附件，或差旅发票为汽车交通费且无附件时，标记为可能存在问题'
    )
    reimbursement_status = models.CharField(
        '报销状态',
        max_length=20,
        choices=REIMBURSEMENT_STATUS,
        default='NOT_SUBMITTED',
        help_text='发票的报销处理状态'
    )
    status_remarks = models.TextField(
        '状态备注',
        blank=True,
        help_text='当状态为"未转入管理员账户"时的说明'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '发票'
        verbose_name_plural = verbose_name

    def __str__(self):
        # 报销人-发票明细-日期-金额
        return f"{self.reimbursement_person} - {self.details} - {self.invoice_date} - {self.amount}"

    def check_potential_issues(self):
        """检查发票是否可能存在问题"""
        # 如果状态是"未转入管理员账户"，标记为可能存在问题
        if self.reimbursement_status == 'NOT_TRANSFERRED':
            self.has_potential_issue = True
            return

        # 其他原有的检查条件
        if not self.attachment:  # 无附件时
            if self.invoice_type == 'DAILY' and float(self.amount) > 1000:
                self.has_potential_issue = True
            elif (self.invoice_type == 'TRAVEL' and 
                  hasattr(self, 'travelinvoice') and 
                  self.travelinvoice.expense_category == 'TRANSPORT' and
                  self.travelinvoice.transport_type == 'BUS'):
                self.has_potential_issue = True
            else:
                self.has_potential_issue = False
        else:
            self.has_potential_issue = False

class TravelInvoice(models.Model):
    """差旅发票扩展信息"""
    TRANSPORT_TYPES = [
        ('TRAIN', '火车'),
        ('PLANE', '飞机'),
        ('BUS', '汽车'),
        ('TAXI', '出租车'),
        ('OTHER', '其他'),
    ]
    
    EXPENSE_CATEGORIES = [
        ('TRANSPORT', '交通'),
        ('ACCOMMODATION', '住宿'),
        ('OTHER', '其他'),
    ]

    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, verbose_name='关联发票')
    traveler = models.CharField(max_length=50, verbose_name='出差人')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    destination = models.CharField(max_length=100, verbose_name='出差地点')
    expense_category = models.CharField(max_length=15, choices=EXPENSE_CATEGORIES, 
                                     verbose_name='费用类别')

    class Meta:
        verbose_name = '差旅发票'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.traveler}的差旅发票 - {self.destination}"

class TransportDetail(models.Model):
    """交通费用详情"""
    SEAT_TYPES = [
        ('TRAIN_SECOND', '高铁二等座'),
        ('TRAIN_FIRST', '高铁一等座'),
        ('TRAIN_BUSINESS', '商务座'),
        ('PLANE_ECONOMY', '经济舱'),
        ('PLANE_BUSINESS', '商务舱'),
        ('OTHER', '其他'),
    ]

    travel_invoice = models.ForeignKey(TravelInvoice, on_delete=models.CASCADE, 
                                     verbose_name='差旅发票')
    transport_type = models.CharField(max_length=10, choices=TravelInvoice.TRANSPORT_TYPES, 
                                    verbose_name='交通类型')
    departure_time = models.DateTimeField(verbose_name='出发时间')
    departure_place = models.CharField(max_length=100, verbose_name='出发地')
    destination = models.CharField(max_length=100, verbose_name='目的地')
    seat_type = models.CharField(max_length=15, choices=SEAT_TYPES, verbose_name='座位类型')

    class Meta:
        verbose_name = '交通明细'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.get_transport_type_display()}: {self.departure_place}-{self.destination}"

class AccommodationDetail(models.Model):
    """住宿费用详情"""
    travel_invoice = models.ForeignKey(TravelInvoice, on_delete=models.CASCADE, 
                                     verbose_name='差旅发票')
    check_in_date = models.DateField(verbose_name='入住日期')
    check_out_date = models.DateField(verbose_name='离店日期')
    hotel_name = models.CharField(max_length=100, verbose_name='酒店名称')

    class Meta:
        verbose_name = '住宿明细'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.hotel_name}: {self.check_in_date} - {self.check_out_date}"

class FundRecord(models.Model):
    """经费流水记录"""
    RECORD_TYPES = [
        ('INCOME', '收入'),
        ('EXPENSE', '支出'),
    ]
    
    amount = models.DecimalField('金额变动', max_digits=10, decimal_places=2,
                                help_text='正值表示收入，负值表示支出')
    balance = models.DecimalField('变动后余额', max_digits=10, decimal_places=2,
                                help_text='经费变动后的余额',
                                default=0)
    record_type = models.CharField('变动类型', max_length=10, choices=RECORD_TYPES)
    description = models.TextField('变动说明')
    record_date = models.DateField('变动日期', 
                                  help_text='实际经费变动的日期',
                                  default=timezone.now)
    created_at = models.DateTimeField('记录时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '经费流水'
        verbose_name_plural = verbose_name
        ordering = ['-record_date', '-created_at']

    def __str__(self):
        return f"{self.record_date} {self.get_record_type_display()}: {self.amount}"

    def save(self, *args, **kwargs):
        # 如果是新记录，自动计算余额
        if not self.pk:
            # 获取最新的记录
            latest_record = FundRecord.objects.order_by('-record_date', '-created_at').first()
            previous_balance = latest_record.balance if latest_record else Decimal('0')
            # 确保 amount 是 Decimal 类型
            self.amount = Decimal(str(self.amount))
            self.balance = previous_balance + self.amount
        super().save(*args, **kwargs)

class ReimbursementRecord(models.Model):
    """报账记录"""
    RECORD_TYPES = [
        ('DAILY', '日常报销'),
        ('TRAVEL', '差旅报销'),
    ]
    
    STATUS_CHOICES = [
        ('SUBMITTED', '已提交'),
        ('COMPLETED', '已报账'),
    ]
    
    reimbursement_date = models.DateField('报账日期', default=timezone.now)
    invoices = models.ManyToManyField(Invoice, verbose_name='关联发票')
    record_type = models.CharField('报账类型', max_length=10, choices=RECORD_TYPES)
    status = models.CharField('报账状态', max_length=10, choices=STATUS_CHOICES, 
                             default='SUBMITTED')
    total_amount = models.DecimalField('总金额', max_digits=10, decimal_places=2, default=0)
    remarks = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '报账记录'
        verbose_name_plural = verbose_name
        ordering = ['-reimbursement_date']

    def __str__(self):
        return f"{self.get_record_type_display()} - {self.reimbursement_date}"

    def update_total_amount(self):
        """更新总金额"""
        self.total_amount = self.invoices.aggregate(total=Sum('amount'))['total'] or 0
        self.save()
