from django.contrib import admin
from .models import ExpenseType, Invoice, TravelInvoice, TransportDetail, AccommodationDetail

@admin.register(ExpenseType)
class ExpenseTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)
    list_filter = ('parent',)

class TransportDetailInline(admin.TabularInline):
    model = TransportDetail
    extra = 1

class AccommodationDetailInline(admin.TabularInline):
    model = AccommodationDetail
    extra = 1

class TravelInvoiceInline(admin.StackedInline):
    model = TravelInvoice
    can_delete = False
    max_num = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'invoice_type', 'amount', 'invoice_date', 
                   'reimbursement_person', 'expense_type')
    list_filter = ('invoice_type', 'invoice_date', 'expense_type')
    search_fields = ('invoice_number', 'reimbursement_person', 'details')
    date_hierarchy = 'invoice_date'
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TravelInvoiceInline]

    def get_inlines(self, request, obj=None):
        if obj and obj.invoice_type == 'TRAVEL':
            return [TravelInvoiceInline]
        return []

@admin.register(TravelInvoice)
class TravelInvoiceAdmin(admin.ModelAdmin):
    list_display = ('traveler', 'destination', 'start_date', 'end_date', 
                   'expense_category', 'get_invoice_number')
    list_filter = ('expense_category', 'start_date')
    search_fields = ('traveler', 'destination', 'invoice__invoice_number')
    inlines = [TransportDetailInline, AccommodationDetailInline]

    def get_invoice_number(self, obj):
        return obj.invoice.invoice_number
    get_invoice_number.short_description = '发票号'
    get_invoice_number.admin_order_field = 'invoice__invoice_number'

@admin.register(TransportDetail)
class TransportDetailAdmin(admin.ModelAdmin):
    list_display = ('get_invoice_number', 'transport_type', 'departure_time', 
                   'departure_place', 'destination', 'seat_type')
    list_filter = ('transport_type', 'seat_type')
    search_fields = ('departure_place', 'destination', 
                    'travel_invoice__invoice__invoice_number')

    def get_invoice_number(self, obj):
        return obj.travel_invoice.invoice.invoice_number
    get_invoice_number.short_description = '发票号'
    get_invoice_number.admin_order_field = 'travel_invoice__invoice__invoice_number'

@admin.register(AccommodationDetail)
class AccommodationDetailAdmin(admin.ModelAdmin):
    list_display = ('get_invoice_number', 'hotel_name', 'check_in_date', 'check_out_date')
    list_filter = ('check_in_date',)
    search_fields = ('hotel_name', 'travel_invoice__invoice__invoice_number')

    def get_invoice_number(self, obj):
        return obj.travel_invoice.invoice.invoice_number
    get_invoice_number.short_description = '发票号'
    get_invoice_number.admin_order_field = 'travel_invoice__invoice__invoice_number'
