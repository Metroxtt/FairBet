from django.contrib import admin
from .models import Account, LedgerEntry


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_type', 'balance', 'version', 'created_at']
    list_filter = ['account_type']
    search_fields = ['user__email', 'user__dni']


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'debit', 'credit', 'hash', 'description', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['id', 'created_at', 'hash', 'previous_hash']
