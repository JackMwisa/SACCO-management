import requests
import uuid
import base64
from django.conf import settings
from django.utils import timezone
from datetime import datetime


class MTNMomoAPI:
    def __init__(self):
        self.base_url = settings.MTN_MOMO_API['BASE_URL']
        self.environment = settings.MTN_MOMO_API['ENVIRONMENT']

    def _get_auth_token(self, api_key, api_secret):
        """Get OAuth2 token for API access"""
        auth_string = f"{api_key}:{api_secret}"
        auth_bytes = auth_string.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')

        headers = {
            'Authorization': f'Basic {base64_auth}',
            'Ocp-Apim-Subscription-Key': api_key
        }

        response = requests.post(
            f"{self.base_url}/collection/token/",
            headers=headers
        )

        if response.status_code == 200:
            return response.json().get('access_token')
        return None

    # def verify_user(self, phone_number):
    #     """Verify mobile money user and get their name"""
    #     token = self._get_auth_token(
    #         settings.MTN_MOMO_API['COLLECTION_PRIMARY_KEY'],
    #         settings.MTN_MOMO_API['COLLECTION_SECONDARY_KEY']
    #     )

    #     if not token:
    #         return None

    #     headers = {
    #         'Authorization': f'Bearer {token}',
    #         'Ocp-Apim-Subscription-Key': settings.MTN_MOMO_API['COLLECTION_PRIMARY_KEY'],
    #         'X-Target-Environment': self.environment
    #     }

    #     response = requests.get(
    #         f"{self.base_url}/v1_0/accountholder/msisdn/{phone_number}/active",
    #         headers=headers
    #     )

    #     if response.status_code == 200:
    #         # Make another call to get user info
    #         info_response = requests.get(
    #             f"{self.base_url}/v1_0/accountholder/msisdn/{phone_number}/basicuserinfo",
    #             headers=headers
    #         )
    #         if info_response.status_code == 200:
    #             return info_response.json()
    #     return None
    def verify_user(self, phone_number):
        """Verify mobile money user by checking if active"""
        token = self._get_auth_token(
            settings.MTN_MOMO_API['COLLECTION_PRIMARY_KEY'],
            settings.MTN_MOMO_API['COLLECTION_SECONDARY_KEY']
        )

        if not token:
            return None

        headers = {
            'Authorization': f'Bearer {token}',
            'Ocp-Apim-Subscription-Key': settings.MTN_MOMO_API['COLLECTION_PRIMARY_KEY'],
            'X-Target-Environment': self.environment
        }

        response = requests.get(
            f"{self.base_url}/v1_0/accountholder/msisdn/{phone_number}/active",
            headers=headers
        )

        if response.status_code == 200 and response.json().get('result') == 'active':
            # Simulate a name (since MTN API doesn't provide it)
            return {"name": "Verified MTN User"}

        return None

    def request_payment(self, amount, phone_number, external_id, payee_note="", payer_message=""):
        """Initiate mobile money payment request"""
        token = self._get_auth_token(
            settings.MTN_MOMO_API['COLLECTION_PRIMARY_KEY'],
            settings.MTN_MOMO_API['COLLECTION_SECONDARY_KEY']
        )

        if not token:
            return None

        headers = {
            'Authorization': f'Bearer {token}',
            'X-Reference-Id': str(uuid.uuid4()),
            'X-Target-Environment': self.environment,
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': settings.MTN_MOMO_API['COLLECTION_PRIMARY_KEY']
        }

        payload = {
            "amount": str(amount),
            "currency": "UGX",
            "externalId": external_id,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": payer_message,
            "payeeNote": payee_note
        }

        # First create request to pay
        response = requests.post(
            f"{self.base_url}/collection/v1_0/requesttopay",
            headers=headers,
            json=payload
        )

        if response.status_code == 202:
            # Check payment status
            transaction_id = headers['X-Reference-Id']
            return self.check_transaction_status(transaction_id)
        return None

    def check_transaction_status(self, transaction_id):
        """Check status of a transaction"""
        token = self._get_auth_token(
            settings.MTN_MOMO_API['COLLECTION_PRIMARY_KEY'],
            settings.MTN_MOMO_API['COLLECTION_SECONDARY_KEY']
        )

        if not token:
            return None

        headers = {
            'Authorization': f'Bearer {token}',
            'Ocp-Apim-Subscription-Key': settings.MTN_MOMO_API['COLLECTION_PRIMARY_KEY'],
            'X-Target-Environment': self.environment
        }

        response = requests.get(
            f"{self.base_url}/collection/v1_0/requesttopay/{transaction_id}",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        return None

    def transfer_money(self, amount, phone_number, external_id, payee_note="", payer_message=""):
        """Transfer money to a mobile money user"""
        token = self._get_auth_token(
            settings.MTN_MOMO_API['DISBURSEMENT_PRIMARY_KEY'],
            settings.MTN_MOMO_API['DISBURSEMENT_SECONDARY_KEY']
        )

        if not token:
            return None

        headers = {
            'Authorization': f'Bearer {token}',
            'X-Reference-Id': str(uuid.uuid4()),
            'X-Target-Environment': self.environment,
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': settings.MTN_MOMO_API['DISBURSEMENT_PRIMARY_KEY']
        }

        payload = {
            "amount": str(amount),
            "currency": "UGX",
            "externalId": external_id,
            "payee": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": payer_message,
            "payeeNote": payee_note
        }

        response = requests.post(
            f"{self.base_url}/disbursement/v1_0/transfer",
            headers=headers,
            json=payload
        )

        if response.status_code == 202:
            transaction_id = headers['X-Reference-Id']
            return self.check_disbursement_status(transaction_id)
        return None

    def check_disbursement_status(self, transaction_id):
        """Check status of a disbursement"""
        token = self._get_auth_token(
            settings.MTN_MOMO_API['DISBURSEMENT_PRIMARY_KEY'],
            settings.MTN_MOMO_API['DISBURSEMENT_SECONDARY_KEY']
        )

        if not token:
            return None

        headers = {
            'Authorization': f'Bearer {token}',
            'Ocp-Apim-Subscription-Key': settings.MTN_MOMO_API['DISBURSEMENT_PRIMARY_KEY'],
            'X-Target-Environment': self.environment
        }

        response = requests.get(
            f"{self.base_url}/disbursement/v1_0/transfer/{transaction_id}",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        return None
