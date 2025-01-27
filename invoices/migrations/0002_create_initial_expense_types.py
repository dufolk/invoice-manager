from django.db import migrations

def create_expense_types(apps, schema_editor):
    ExpenseType = apps.get_model('invoices', 'ExpenseType')
    
    initial_types = {
        'DAILY': [
            '书报杂志订阅费',
            '印刷费',
            '邮寄费',
            '仪器设备维修费',
            '会议费',
            '专用材料费',
            '交通费',
            '其他-日常'
        ],
        'TRAVEL': [
            '交通费',
            '住宿费',
            '其他-差旅'
        ]
    }
    
    for category, names in initial_types.items():
        for name in names:
            ExpenseType.objects.create(
                name=name,
                category=category
            )

def reverse_expense_types(apps, schema_editor):
    ExpenseType = apps.get_model('invoices', 'ExpenseType')
    ExpenseType.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('invoices', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_expense_types, reverse_expense_types),
    ] 