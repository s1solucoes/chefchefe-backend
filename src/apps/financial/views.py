from django.shortcuts import render
from django.views.generic import TemplateView

from apps.products.models import Bill, Order
from apps.financial.models import Cashier, PaymentMethod, Transaction
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

        closed_bills = bills.filter(
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

        canceled_orders = Order.objects.filter(
            bill__in=bills,
            status='CANCELED'
        ).values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_revenue')

        payment_methods = Transaction.objects.filter(
            sale__cashier_id=cashier_id,
            type='SALE',
            status='COMPLETED'
        ).values('payment_method__method').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')

        payment_methods_exchange = Transaction.objects.filter(
            sale__cashier_id=cashier_id,
            type='EXCHANGE',
            status='COMPLETED'
        ).values('payment_method__method').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')

        final_methods = []
        for method in payment_methods:
            data = {
                'method': PaymentMethod.get_display(method['payment_method__method']),
                'total_amount': method['total_amount'],
                'transaction_count': method['transaction_count'],
                'exchange_amount': payment_methods_exchange.filter(payment_method__method=method['payment_method__method']).aggregate(total_exchange=Sum('amount'))['total_exchange'] or 0
            }
            data['net_amount'] = data['total_amount'] + data['exchange_amount']
            final_methods.append(data)

# ({
#             'bills_count': bills.count(),
#             'closed_bills_count': closed_bills.count(),
#             'total_revenue': bills.aggregate(total_revenue=Sum('sale__balance'))['total_revenue'] or 0,
#             'orders_stats': orders_stats,
#             'canceled_orders': canceled_orders,
#             'payment_methods': payment_methods,
#             'payment_methods_exchange': payment_methods_exchange,
#             'final_methods': final_methods
#         })

        context['bills_count'] = bills.count()
        context['closed_bills_count'] = closed_bills.count()
        context['total_revenue'] = bills.aggregate(total_revenue=Sum('sale__balance'))['total_revenue'] or 0
        context['orders_stats'] = orders_stats
        context['canceled_orders'] = canceled_orders
        context['payment_methods'] = payment_methods
        
        context['payment_methods_exchange'] = payment_methods_exchange
        context['final_methods'] = final_methods
        context['date'] = cashier.created if cashier else None
        return context