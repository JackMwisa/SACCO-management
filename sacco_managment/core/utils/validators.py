"""
Input validation and sanitization utilities for SACCO management system.
"""
import re
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags


def sanitize_text(value, max_length=None):
    """
    Sanitize text input by stripping HTML tags and trimming whitespace.
    """
    if value is None:
        return ''
    # Strip HTML tags to prevent XSS
    cleaned = strip_tags(str(value)).strip()
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def validate_phone_number(phone):
    """
    Validate Ugandan phone number format.
    Accepts formats: 0771234567, +256771234567, 256771234567
    """
    if not phone:
        raise ValidationError("Phone number is required.")

    # Remove spaces, dashes, and parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', str(phone))

    # Ugandan phone number patterns
    patterns = [
        r'^0[3-9]\d{8}$',  # Local format: 0771234567
        r'^\+?256[3-9]\d{8}$',  # International: +256771234567 or 256771234567
    ]

    for pattern in patterns:
        if re.match(pattern, cleaned):
            return cleaned

    raise ValidationError("Invalid phone number format. Use format: 0771234567 or +256771234567")


def normalize_phone_number(phone):
    """
    Normalize phone number to international format without + sign.
    """
    cleaned = re.sub(r'[\s\-\(\)\+]', '', str(phone))

    # Convert local format to international
    if cleaned.startswith('0'):
        cleaned = '256' + cleaned[1:]

    return cleaned


def validate_amount(value, min_amount=0, max_amount=None, field_name="Amount"):
    """
    Validate monetary amount.
    """
    try:
        if value is None or value == '':
            raise ValidationError(f"{field_name} is required.")

        amount = Decimal(str(value))

        if amount < min_amount:
            raise ValidationError(f"{field_name} must be at least {min_amount:,}")

        if max_amount and amount > max_amount:
            raise ValidationError(f"{field_name} cannot exceed {max_amount:,}")

        # Check for reasonable precision (2 decimal places max)
        if amount != amount.quantize(Decimal('0.01')):
            raise ValidationError(f"{field_name} can have at most 2 decimal places")

        return amount

    except InvalidOperation:
        raise ValidationError(f"Invalid {field_name.lower()}. Please enter a valid number.")


def validate_account_number(account_number):
    """
    Validate SACCO account number format.
    """
    if not account_number:
        raise ValidationError("Account number is required.")

    # Expected format: 217 prefix + 10 digits
    cleaned = str(account_number).strip()

    if not cleaned.startswith('217'):
        raise ValidationError("Invalid account number format.")

    if not cleaned[3:].isdigit() or len(cleaned) != 13:
        raise ValidationError("Invalid account number format.")

    return cleaned


def validate_pin(pin):
    """
    Validate PIN format (4 digits).
    """
    if not pin:
        raise ValidationError("PIN is required.")

    cleaned = str(pin).strip()

    if not cleaned.isdigit() or len(cleaned) != 4:
        raise ValidationError("PIN must be exactly 4 digits.")

    return cleaned


def validate_national_id(id_number):
    """
    Validate Ugandan National ID format.
    Format: CM followed by 12 alphanumeric characters
    """
    if not id_number:
        raise ValidationError("National ID is required.")

    cleaned = str(id_number).strip().upper()

    if not re.match(r'^CM[A-Z0-9]{12}$', cleaned):
        raise ValidationError("Invalid National ID format. Expected format: CM followed by 12 characters.")

    return cleaned


def validate_email(email):
    """
    Validate email format.
    """
    if not email:
        raise ValidationError("Email is required.")

    cleaned = str(email).strip().lower()

    # Basic email validation regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, cleaned):
        raise ValidationError("Invalid email format.")

    return cleaned


def validate_name(name, field_name="Name"):
    """
    Validate person's name - only letters, spaces, hyphens, and apostrophes.
    """
    if not name:
        raise ValidationError(f"{field_name} is required.")

    cleaned = sanitize_text(name, max_length=100)

    # Allow letters (including unicode), spaces, hyphens, apostrophes
    if not re.match(r"^[\w\s\-']+$", cleaned, re.UNICODE):
        raise ValidationError(f"{field_name} contains invalid characters.")

    if len(cleaned) < 2:
        raise ValidationError(f"{field_name} is too short.")

    return cleaned


class InputSanitizer:
    """
    Class to sanitize and validate form inputs.
    Usage:
        sanitizer = InputSanitizer(request.POST)
        amount = sanitizer.get_amount('amount', min_amount=1000)
        phone = sanitizer.get_phone('phone_number')
    """

    def __init__(self, data):
        self.data = data
        self.errors = {}

    def get_text(self, key, default='', max_length=None, required=False):
        """Get sanitized text input."""
        value = self.data.get(key, default)
        result = sanitize_text(value, max_length)

        if required and not result:
            self.errors[key] = f"{key.replace('_', ' ').title()} is required."
            return default

        return result

    def get_amount(self, key, default=Decimal('0'), min_amount=0, max_amount=None, required=True):
        """Get validated amount."""
        value = self.data.get(key, '')
        try:
            return validate_amount(value, min_amount, max_amount, key.replace('_', ' ').title())
        except ValidationError as e:
            if required:
                self.errors[key] = str(e.message)
            return default

    def get_phone(self, key, required=True):
        """Get validated phone number."""
        value = self.data.get(key, '')
        try:
            return validate_phone_number(value)
        except ValidationError as e:
            if required:
                self.errors[key] = str(e.message)
            return ''

    def get_pin(self, key, required=True):
        """Get validated PIN."""
        value = self.data.get(key, '')
        try:
            return validate_pin(value)
        except ValidationError as e:
            if required:
                self.errors[key] = str(e.message)
            return ''

    def has_errors(self):
        """Check if there are validation errors."""
        return bool(self.errors)

    def get_errors(self):
        """Get all validation errors."""
        return self.errors
