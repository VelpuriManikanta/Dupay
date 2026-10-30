"""Transaction API routes."""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.TransactionInitiateView.as_view(), name="transaction-initiate"),
    path("<uuid:reference>/", views.TransactionDetailView.as_view(), name="transaction-detail"),
    path("<uuid:reference>/status/", views.TransactionStatusView.as_view(), name="transaction-status"),
    path("<uuid:reference>/events/", views.TransactionHistoryView.as_view(), name="transaction-history"),
    path("list/", views.TransactionListView.as_view(), name="transaction-list"),
]