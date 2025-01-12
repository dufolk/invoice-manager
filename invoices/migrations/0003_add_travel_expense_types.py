from django.db import migrations

def create_travel_expense_types(apps, schema_editor):
    ExpenseType = apps.get_model('invoices', 'ExpenseType')
    
    # 创建差旅费用类型
    ExpenseType.objects.get_or_create(
        name='交通费',
        category='TRAVEL'
    )
    
    ExpenseType.objects.get_or_create(
        name='住宿费',
        category='TRAVEL'
    )
    
    ExpenseType.objects.get_or_create(
        name='其他差旅费',
        category='TRAVEL'
    )

def reverse_func(apps, schema_editor):
    ExpenseType = apps.get_model('invoices', 'ExpenseType')
    ExpenseType.objects.filter(
        name__in=['交通费', '住宿费', '其他差旅费'],
        category='TRAVEL'
    ).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('invoices', '0002_invoice_remarks_alter_invoice_details'),
    ]

    operations = [
        migrations.RunPython(create_travel_expense_types, reverse_func),
    ] 