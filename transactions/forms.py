from django import forms
from .models import Transaction, UserBankAccount

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput() 

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):
    def clean_amount(self):
        min_deposit_amount = 100
        amount = self.cleaned_data.get('amount') 
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount


class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance 
        amount = self.cleaned_data.get('amount')
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )

        if amount > balance: 
            raise forms.ValidationError(
                f'You have {balance} $ in your account. '
                'You can not withdraw more than your account balance'
            )

        return amount



class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        return amount

class MoneyTransferForm(forms.ModelForm):
    receiver_account_id = forms.IntegerField(label='Receiver Account ID')
    amount = forms.DecimalField(label='Amount', decimal_places=2, max_digits=12)

    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'  
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account', None)
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

        if self.account:
            self.fields['receiver_account_id'].queryset = UserBankAccount.objects.exclude(user=self.account.user)
        else:
            self.fields['receiver_account_id'].queryset = UserBankAccount.objects.none()

    def clean_receiver_account_id(self):
        receiver_account_id = self.cleaned_data.get('receiver_account_id')
        print(f"Receiver Account ID: {receiver_account_id}")

        try:
            receiver_account = UserBankAccount.objects.get(id=receiver_account_id)
            print(f"Receiver Account: {receiver_account}")
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError(f"Invalid receiver account ID: {receiver_account_id}")
        
        if receiver_account.user == self.account.user:
            raise forms.ValidationError("Cannot transfer money to your own account.")

        return receiver_account_id

    def save(self, commit=True):
        if self.account:
            self.instance.account = self.account
            self.instance.balance_after_transaction = self.account.balance

        receiver_account_id = self.cleaned_data.get('receiver_account_id')
        receiver_account = UserBankAccount.objects.get(id=receiver_account_id)
        self.instance.receiver = receiver_account

        return super().save()



