# Generated by Django 5.1.6 on 2025-05-02 09:41

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("financial_services", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="cryptotransaction",
            options={
                "ordering": ["-timestamp"],
                "verbose_name": "Crypto Transaction",
                "verbose_name_plural": "Crypto Transactions",
            },
        ),
        migrations.AlterModelOptions(
            name="cryptowallet",
            options={
                "verbose_name": "Crypto Wallet",
                "verbose_name_plural": "Crypto Wallets",
            },
        ),
        migrations.AddField(
            model_name="cryptotransaction",
            name="related_transaction",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="related_transactions",
                to="financial_services.cryptotransaction",
            ),
        ),
        migrations.AddField(
            model_name="cryptowallet",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="cryptotransaction",
            name="amount",
            field=models.DecimalField(
                decimal_places=8,
                max_digits=20,
                validators=[django.core.validators.MinValueValidator(Decimal("1E-8"))],
            ),
        ),
        migrations.AlterField(
            model_name="cryptotransaction",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("COMPLETED", "Completed"),
                    ("FAILED", "Failed"),
                    ("CANCELLED", "Cancelled"),
                ],
                default="PENDING",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="cryptotransaction",
            name="timestamp",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="cryptotransaction",
            name="wallet",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transactions",
                to="financial_services.cryptowallet",
            ),
        ),
        migrations.AlterField(
            model_name="cryptowallet",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="wallets",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
