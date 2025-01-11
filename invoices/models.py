from django.db import models

class ExpenseType(models.Model):
    """费用类型模型"""
    name = models.CharField(max_length=50, verbose_name='类型名称')
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
        ('DAILY', '日常'),
        ('TRAVEL', '差旅'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='发票号')
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPES, verbose_name='发票类型')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='发票金额')
    details = models.TextField('报销内容明细', blank=True)
    remarks = models.TextField('备注', blank=True)
    invoice_date = models.DateField(verbose_name='发票日期')
    image = models.ImageField(upload_to='invoice_images/', verbose_name='发票照片')
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.PROTECT, verbose_name='费用类型')
    reimbursement_person = models.CharField(max_length=50, verbose_name='报销人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

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
