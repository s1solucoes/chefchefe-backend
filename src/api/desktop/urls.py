from rest_framework.routers import DefaultRouter
from .viewsets import (
    ProductViewSet,
    CreateOrderViewSet,
    BillViewSet,
    TableViewSet,
    RestaurantViewSet,
    BillGroupViewSet,
    CashierViewSet,
    PaymentMethodViewSet,
    PaymentMethodsStatsViewSet,
    FinishBillsViewSet,
    SaleViewSet,
    TransactionViewSet,
    PrintJobViewSet,
    ImportProductsViewSet,
    CashierStats,
    SendOrderSaleViewSet
    
)
router_desktop = DefaultRouter()
router_desktop.register(r'products', ProductViewSet, basename='desktop-product')
router_desktop.register(r'orders', CreateOrderViewSet, basename='desktop-order')
router_desktop.register(r'bills', BillViewSet, basename='desktop-bill')
router_desktop.register(r'tables', TableViewSet, basename='desktop-table')
router_desktop.register(r'restaurant', RestaurantViewSet, basename='desktop-restaurant')
router_desktop.register(r'bill-groups', BillGroupViewSet, basename='desktop-bill-group')
router_desktop.register(r'cashiers', CashierViewSet, basename='desktop-cashier')
router_desktop.register(r'payment-methods', PaymentMethodViewSet, basename='desktop-payment-method')
router_desktop.register(r'payment-methods-stats', PaymentMethodsStatsViewSet, basename='desktop-payment-methods-stats')
router_desktop.register(r'finish-bills', FinishBillsViewSet, basename='desktop-finish-bills')
router_desktop.register(r'sales', SaleViewSet, basename='desktop-sale')
router_desktop.register(r'transactions', TransactionViewSet, basename='desktop-transaction')
router_desktop.register(r'print-jobs', PrintJobViewSet, basename='desktop-print-job')
router_desktop.register(r'import-products', ImportProductsViewSet, basename='desktop-import-products')
router_desktop.register(r'cashier-stats', CashierStats, basename='desktop-cashier-stats')
router_desktop.register(r'send-counter-sale', SendOrderSaleViewSet, basename='desktop-send-order-sale')