import requests
import json
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class PaymentGateway:
    """
    Payment Gateway service for handling online payments
    Supports multiple Iranian payment gateways like ZarinPal, IDPay, etc.
    """
    
    def __init__(self, gateway_type='zarinpal'):
        self.gateway_type = gateway_type
        self.config = self._get_gateway_config()
    
    def _get_gateway_config(self):
        """Get configuration for the selected payment gateway"""
        gateway_configs = {
            'zarinpal': {
                'merchant_id': getattr(settings, 'ZARINPAL_MERCHANT_ID', 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'),
                'request_url': 'https://api.zarinpal.com/pg/v4/payment/request.json',
                'verify_url': 'https://api.zarinpal.com/pg/v4/payment/verify.json',
                'gateway_url': 'https://www.zarinpal.com/pg/StartPay/',
                'sandbox_request_url': 'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
                'sandbox_verify_url': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
                'sandbox_gateway_url': 'https://sandbox.zarinpal.com/pg/StartPay/',
            },
            'idpay': {
                'api_key': getattr(settings, 'IDPAY_API_KEY', 'your-api-key'),
                'request_url': 'https://api.idpay.ir/v1.1/payment',
                'verify_url': 'https://api.idpay.ir/v1.1/payment/verify',
                'sandbox_request_url': 'https://api.idpay.ir/v1.1/payment',
                'sandbox_verify_url': 'https://api.idpay.ir/v1.1/payment/verify',
            }
        }
        
        config = gateway_configs.get(self.gateway_type, gateway_configs['zarinpal'])
        
        # Use sandbox URLs if ZARINPAL_SANDBOX is True
        if getattr(settings, 'ZARINPAL_SANDBOX', True):
            if 'sandbox_request_url' in config:
                config['request_url'] = config['sandbox_request_url']
            if 'sandbox_verify_url' in config:
                config['verify_url'] = config['sandbox_verify_url']
            if 'sandbox_gateway_url' in config:
                config['gateway_url'] = config['sandbox_gateway_url']
        
        return config
    
    def create_payment_request(self, amount, description, callback_url, mobile=None, email=None):
        """
        Create a payment request with the gateway
        Returns: (success, data) tuple
        """
        try:
            if self.gateway_type == 'zarinpal':
                return self._zarinpal_request(amount, description, callback_url, mobile, email)
            elif self.gateway_type == 'idpay':
                return self._idpay_request(amount, description, callback_url, mobile, email)
            else:
                return False, {'error': 'Unsupported gateway type'}
        except Exception as e:
            logger.error(f"Payment gateway request error: {str(e)}")
            return False, {'error': str(e)}
    
    def verify_payment(self, authority, amount):
        """
        Verify a payment with the gateway
        Returns: (success, data) tuple
        """
        try:
            if self.gateway_type == 'zarinpal':
                return self._zarinpal_verify(authority, amount)
            elif self.gateway_type == 'idpay':
                return self._idpay_verify(authority, amount)
            else:
                return False, {'error': 'Unsupported gateway type'}
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return False, {'error': str(e)}
    
    def _zarinpal_request(self, amount, description, callback_url, mobile=None, email=None):
        """ZarinPal payment request"""
        # Convert Decimal to int for ZarinPal API (amounts should be in Tomans)
        if hasattr(amount, 'to_integral_value'):  # Check if it's a Decimal
            amount = int(amount)
        elif isinstance(amount, float):
            amount = int(amount)
        
        data = {
            'merchant_id': self.config['merchant_id'],
            'amount': amount,
            'description': description,
            'callback_url': callback_url,
        }
        
        if mobile:
            data['mobile'] = mobile
        if email:
            data['email'] = email
        
        response = requests.post(
            self.config['request_url'],
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('data', {}).get('code') == 100:
                authority = result['data']['authority']
                gateway_url = f"{self.config['gateway_url']}{authority}"
                return True, {
                    'authority': authority,
                    'gateway_url': gateway_url
                }
            else:
                return False, {'error': result.get('errors', 'Unknown error')}
        else:
            return False, {'error': f'HTTP {response.status_code}'}
    
    def _zarinpal_verify(self, authority, amount):
        """ZarinPal payment verification"""
        # Convert Decimal to int for ZarinPal API (amounts should be in Tomans)
        if hasattr(amount, 'to_integral_value'):  # Check if it's a Decimal
            amount = int(amount)
        elif isinstance(amount, float):
            amount = int(amount)
            
        data = {
            'merchant_id': self.config['merchant_id'],
            'amount': amount,
            'authority': authority
        }
        
        response = requests.post(
            self.config['verify_url'],
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('data', {}).get('code') == 100:
                return True, {
                    'ref_id': result['data']['ref_id'],
                    'card_pan': result['data'].get('card_pan'),
                    'card_hash': result['data'].get('card_hash'),
                    'fee_type': result['data'].get('fee_type'),
                    'fee': result['data'].get('fee')
                }
            else:
                return False, {'error': result.get('errors', 'Verification failed')}
        else:
            return False, {'error': f'HTTP {response.status_code}'}
    
    def _idpay_request(self, amount, description, callback_url, mobile=None, email=None):
        """IDPay payment request"""
        data = {
            'order_id': f"order_{int(time.time())}",
            'amount': amount,
            'desc': description,
            'callback': callback_url,
        }
        
        if mobile:
            data['phone'] = mobile
        if email:
            data['mail'] = email
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.config['api_key']
        }
        
        response = requests.post(self.config['request_url'], json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            return True, {
                'authority': result['id'],
                'gateway_url': result['link']
            }
        else:
            result = response.json() if response.content else {'message': 'Unknown error'}
            return False, {'error': result.get('message', 'Request failed')}
    
    def _idpay_verify(self, authority, amount):
        """IDPay payment verification"""
        data = {
            'id': authority,
            'order_id': f"order_{authority}"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.config['api_key']
        }
        
        response = requests.post(self.config['verify_url'], json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return True, {
                'ref_id': result.get('track_id'),
                'card_pan': result.get('payment', {}).get('card_no'),
                'amount': result.get('amount'),
                'status': result.get('status')
            }
        else:
            result = response.json() if response.content else {'message': 'Unknown error'}
            return False, {'error': result.get('message', 'Verification failed')}

import time 