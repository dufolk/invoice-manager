from django.db import migrations

def create_expense_types(apps, schema_editor):
    ExpenseType = apps.get_model('invoices', 'ExpenseType')
    
    # 日常发票费用类型
    daily_types = [
        '书报杂志订阅费',
        '印刷费',
        '邮寄费',
        '仪器设备维修费',
        '会议费',
        '专用材料费',
        '交通费',
        '其他'
    ]
    
    for name in daily_types:
        ExpenseType.objects.create(
            name=name,
            category='DAILY'
        )
    
    # 差旅发票费用类型
    travel_types = [
        '交通费',
        '住宿费',
        '其他'
    ]
    
    for name in travel_types:
        ExpenseType.objects.create(
            name=name,
            category='TRAVEL'
        )

def delete_expense_types(apps, schema_editor):
    ExpenseType = apps.get_model('invoices', 'ExpenseType')
    ExpenseType.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0002_invoice_remarks_alter_invoice_details'),  # 确保这里是正确的依赖
    ]

    operations = [
        migrations.RunPython(create_expense_types, delete_expense_types),
    ] 