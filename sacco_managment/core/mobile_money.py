
import requests
from django.conf import settings

class MobileMoneyVerifier:
    @staticmethod
    def verify_number(phone_number, provider):
        if provider == 'MTN':
            return MobileMoneyVerifier._verify_mtn(phone_number)
        elif provider == 'Airtel':
            return MobileMoneyVerifier._verify_airtel(phone_number)
        return {'valid': False, 'message': 'Unsupported provider'}

    @staticmethod
    def _verify_mtn(phone_number):
        headers = {
            'Authorization': f'Bearer {settings.MTN_API_KEY}',
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': settings.MTN_SUBSCRIPTION_KEY
        }
        
        try:
            response = requests.get(
                f'https://sandbox.momodeveloper.mtn.com/v1_0/accountholder/msisdn/{phone_number}/active',
                headers=headers
            )
            
            if response.status_code == 200:
                return {
                    'valid': True,
                    'name': response.json().get('name', 'Verified User'),
                    'provider': 'MTN'
                }
            return {'valid': False, 'message': 'Number not verified'}
            
        except Exception as e:
            return {'valid': False, 'message': str(e)}

    @staticmethod
    def _verify_airtel(phone_number):
        headers = {
            'Authorization': f'Bearer {settings.AIRTEL_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                'https://openapi.airtel.africa/auth/oauth2/token',
                headers=headers,
                data={'grant_type': 'client_credentials'}
            )
            
            if response.status_code == 200:
                token = response.json().get('access_token')
                headers['Authorization'] = f'Bearer {token}'
                
                response = requests.get(
                    f'https://openapi.airtel.africa/standard/v1/users/{phone_number}',
                    headers=headers
                )
                
                if response.status_code == 200:
                    return {
                        'valid': True,
                        'name': response.json().get('name', 'Verified User'),
                        'provider': 'Airtel'
                    }
            return {'valid': False, 'message': 'Number not verified'}
            
        except Exception as e:
            return {'valid': False, 'message': str(e)}