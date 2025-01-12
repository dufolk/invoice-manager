from django.db import models
from django.core.validators import FileExtensionValidator

class ExpenseType(models.Model):
    """费用类型模型"""
    CATEGORY_CHOICES = [
        ('DAILY', '日常费用'),
        ('TRAVEL', '差旅费用'),
        ('BOTH', '通用'),
    ]
    
    name = models.CharField(max_length=50, verbose_name='类型名称')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='BOTH', 
                              verbose_name='费用分类')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              verbose_name='父类型')

    class Meta:
        verbose_name = '费用类型'
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name

class Invoice(models.Model):
    """发票基础模型"""
    INVOICE_TYPES = [
        ('DAILY', '日常发票'),
        ('TRAVEL', '差旅发票'),
    ]
    
    invoice_number = models.CharField('发票号码', max_length=50, unique=True)
    invoice_type = models.CharField('发票类型', max_length=10, choices=INVOICE_TYPES)
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.PROTECT, verbose_name='费用类型')
    amount = models.DecimalField('金额', max_digits=10, decimal_places=2)
    invoice_date = models.DateField('发票日期')
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
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '发票'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.invoice_number} - {self.reimbursement_person}"

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
