from django.shortcuts import render
from django.views.generic import TemplateView

from apps.products.models import Bill, Order
from apps.financial.models import Cashier, PaymentMethod, Sale, Transaction
from django.db.models import Sum, Count, Q
class StatsView(TemplateView):
    template_name = 'stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cashier_id = self.request.GET.get('cashier_id')
        cashier = Cashier.objects.filter(id=cashier_id).first()
        bills = Bill.objects.filter(
            Q(sale__cashier_id=cashier_id),
            is_open=False,
        ).select_related('sale')

        closed_bills = Bill.objects.filter(
            is_open=False,
            cashier_id=cashier_id, 
            sale__isnull=True
        ).select_related('sale')
        orders_stats = Order.objects.filter(
            bill__in=bills,
        ).exclude(status='CANCELED').values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_revenue')
        orders = Order.objects.filter(
            bill__in=bills,
        ).exclude(status='CANCELED')
        canceled_orders = Order.objects.filter(
            bill__in=bills,
            status='CANCELED'
        )
        sales = Sale.objects.filter(
            cashier_id=cashier_id,
        )

        payment_methods = Transaction.objects.filter(
            sale__cashier_id=cashier_id,
        ).values('payment_method__method').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')

        for pay in payment_methods:
            pay['method'] = PaymentMethod.get_display(pay['payment_method__method'])

        emploee_stats = Order.objects.filter(
            bill__in=bills,
        ).exclude(status='CANCELED').values('launched_by__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price'),
        ).order_by('-total_revenue')
        sale_stats = Sale.objects.filter(
            cashier_id=cashier_id,
        ).aggregate(
            total_revenue=Sum('total'),
            total_sub_total=Sum('subtotal'),
        )
        context['bills_count'] = bills.count()
        context['closed_bills_count'] = closed_bills.count()
        context['total_revenue'] = sales.aggregate(total_revenue=Sum('balance'))['total_revenue'] or 0
        context['orders_stats'] = orders_stats
        context['orders'] = orders
        context['canceled_orders'] = canceled_orders
        context['final_methods'] = payment_methods
        context['date'] = cashier.created if cashier else None
        context['close_date'] = cashier.closed_at if cashier else None
        context['cashier'] = cashier
        context['employee_stats'] = emploee_stats
        context['total_tax'] =  sale_stats['total_revenue'] - sale_stats['total_sub_total'] if sale_stats['total_revenue'] and sale_stats['total_sub_total'] else 0

        return context