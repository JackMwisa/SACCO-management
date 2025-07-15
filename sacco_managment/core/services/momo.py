import requests
from django.conf import settings
from requests.exceptions import RequestException

class MTNMomoService:
    BASE_URL = "https://sandbox.momodeveloper.mtn.com"  # Production: "https://api.mtn.com"
    
    def __init__(self):
        self.subscription_key = settings.MOMO_SUBSCRIPTION_KEY
        self.callback_url = settings.MOMO_CALLBACK_URL
        
    def _get_auth_token(self):
        """Get OAuth2 token for API access"""
        url = f"{self.BASE_URL}/collection/token/"
        headers = {
            'Authorization': f'Basic {settings.MOMO_API_SECRET}',
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()['access_token']
    
    def verify_user(self, phone_number):
        """Verify mobile money user details"""
        url = f"{self.BASE_URL}/v1_0/accountholder/msisdn/{phone_number}/active"
        headers = {
            'Authorization': f'Bearer {self._get_auth_token()}',
            'X-Target-Environment': settings.MOMO_ENVIRONMENT,
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return {
                    'verified': True,
                    'name': response.json().get('name'),
                    'provider': 'MTN'
                }
            return {'verified': False, 'error': 'Number not registered with MoMo'}
        except RequestException as e:
            raise Exception(f"Verification failed: {str(e)}")

    def initiate_payment(self, amount, phone, reference):
        """Initiate USSD/QR payment request"""
        url = f"{self.BASE_URL}/collection/v1_0/requesttopay"
        headers = {
            'Authorization': f'Bearer {self._get_auth_token()}',
            'X-Reference-Id': reference,
            'X-Target-Environment': settings.MOMO_ENVIRONMENT,
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            "amount": str(amount),
            "currency": "UGX",
            "externalId": reference[:50],  # Truncate if needed
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone
            },
            "payerMessage": "Payment to your SACCO",
            "payeeNote": f"Deposit ref: {reference}"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 202:
            return {
                'success': True,
                'ussd_code': f"*165*1*{reference}#",
                'qr_data': f"{phone},{amount},{reference}"
            }
        raise Exception(f"Payment initiation failed: {response.text}")