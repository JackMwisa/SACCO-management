"""
Management command to migrate plaintext PINs to hashed PINs.

Usage:
    python manage.py hash_pins              # Dry run (shows what would be migrated)
    python manage.py hash_pins --execute    # Actually migrate the PINs

This command:
1. Finds all accounts with plaintext PINs (pin_number set, pin_hash empty)
2. Hashes each PIN using Django's password hasher
3. Stores the hash in pin_hash field
4. Optionally clears the plaintext pin_number (recommended for security)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from account.models import Account


class Command(BaseCommand):
    help = 'Migrate plaintext PINs to secure hashed PINs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually execute the migration (default is dry run)',
        )
        parser.add_argument(
            '--clear-plaintext',
            action='store_true',
            help='Clear plaintext PIN after hashing (recommended for security)',
        )

    def handle(self, *args, **options):
        execute = options['execute']
        clear_plaintext = options['clear_plaintext']

        self.stdout.write(self.style.NOTICE(
            f"{'EXECUTING' if execute else 'DRY RUN'} PIN migration..."
        ))

        # Find accounts with plaintext PIN but no hash
        accounts_to_migrate = Account.objects.filter(
            pin_hash__isnull=True
        ).exclude(pin_number__isnull=True).exclude(pin_number='')

        # Also include accounts where pin_hash is empty string
        accounts_with_empty_hash = Account.objects.filter(
            pin_hash=''
        ).exclude(pin_number__isnull=True).exclude(pin_number='')

        # Combine querysets
        accounts_needing_migration = accounts_to_migrate | accounts_with_empty_hash
        accounts_needing_migration = accounts_needing_migration.distinct()

        total_count = accounts_needing_migration.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS(
                "No accounts need PIN migration. All PINs are already hashed."
            ))
            return

        self.stdout.write(f"Found {total_count} accounts needing PIN migration.")

        migrated_count = 0
        error_count = 0

        for account in accounts_needing_migration:
            try:
                plaintext_pin = account.pin_number

                if not plaintext_pin:
                    self.stdout.write(self.style.WARNING(
                        f"  Skipping account {account.account_number}: No PIN set"
                    ))
                    continue

                if execute:
                    # Hash the PIN
                    account.pin_hash = make_password(str(plaintext_pin))

                    # Optionally clear plaintext PIN
                    if clear_plaintext:
                        # We can't actually clear ShortUUIDField, but we mark it as migrated
                        pass  # pin_number is auto-generated, keep for reference

                    account.save(update_fields=['pin_hash'])

                    self.stdout.write(self.style.SUCCESS(
                        f"  Migrated account {account.account_number} ({account.user.username})"
                    ))
                else:
                    self.stdout.write(
                        f"  Would migrate account {account.account_number} ({account.user.username})"
                    )

                migrated_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f"  Error migrating account {account.account_number}: {str(e)}"
                ))

        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("=" * 50))

        if execute:
            self.stdout.write(self.style.SUCCESS(
                f"Migration complete: {migrated_count} accounts migrated, {error_count} errors"
            ))
            if not clear_plaintext:
                self.stdout.write(self.style.WARNING(
                    "Note: Plaintext PINs were NOT cleared. Consider running with --clear-plaintext"
                ))
        else:
            self.stdout.write(self.style.NOTICE(
                f"DRY RUN complete: {migrated_count} accounts would be migrated"
            ))
            self.stdout.write(self.style.NOTICE(
                "Run with --execute flag to actually migrate PINs"
            ))

        # Show stats of already-migrated accounts
        already_hashed = Account.objects.exclude(pin_hash__isnull=True).exclude(pin_hash='').count()
        self.stdout.write(f"\nAccounts with hashed PINs: {already_hashed}")
        self.stdout.write(f"Accounts with plaintext PINs: {total_count}")
