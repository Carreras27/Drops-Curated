"""
Gupshup WhatsApp Business API Integration
Handles OTP sending and alert notifications via WhatsApp
"""

import os
import json
import logging
import requests
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Gupshup Configuration
GUPSHUP_API_KEY = os.environ.get('GUPSHUP_API_KEY', '')
GUPSHUP_APP_NAME = os.environ.get('GUPSHUP_APP_NAME', 'DropsCurated')
GUPSHUP_SOURCE_NUMBER = os.environ.get('GUPSHUP_SOURCE_NUMBER', '919700771000')
GUPSHUP_API_URL = os.environ.get('GUPSHUP_API_URL', 'https://api.gupshup.io/wa/api/v1')

# Template IDs (will be updated after templates are approved)
TEMPLATE_OTP = "otp_code"
TEMPLATE_PRICE_DROP = "price_drop"
TEMPLATE_NEW_DROP = "new_drop"


class GupshupClient:
    """Client for Gupshup WhatsApp Business API"""
    
    def __init__(self):
        self.api_key = GUPSHUP_API_KEY
        self.app_name = GUPSHUP_APP_NAME
        self.source_number = GUPSHUP_SOURCE_NUMBER
        self.api_url = GUPSHUP_API_URL
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to required format (without + or spaces)"""
        # Remove all non-digit characters
        cleaned = ''.join(c for c in phone if c.isdigit())
        
        # Add country code if not present (assume India)
        if len(cleaned) == 10:
            cleaned = f"91{cleaned}"
        
        return cleaned
    
    def send_template_message(
        self,
        destination: str,
        template_id: str,
        params: list = None
    ) -> Tuple[bool, str]:
        """
        Send a template message via WhatsApp
        
        Args:
            destination: Recipient phone number
            template_id: Template name/ID
            params: List of template parameters
            
        Returns:
            Tuple of (success, message_id or error)
        """
        destination = self._normalize_phone(destination)
        
        template_data = {
            "id": template_id,
        }
        
        if params:
            template_data["params"] = params
        
        payload = {
            "source": self.source_number,
            "destination": destination,
            "template": json.dumps(template_data),
            "src.name": self.app_name
        }
        
        try:
            logger.info(f"Sending template message to {destination} with template {template_id}")
            
            response = requests.post(
                f"{self.api_url}/template/msg",
                headers=self.headers,
                data=payload,
                timeout=30
            )
            
            result = response.json()
            
            if response.status_code in [200, 201, 202]:
                message_id = result.get("messageId", "")
                logger.info(f"Template message sent successfully. Message ID: {message_id}")
                return True, message_id
            else:
                error_msg = result.get("message", str(result))
                logger.error(f"Gupshup API error: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout sending message to {destination}")
            return False, "Request timeout"
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False, str(e)
    
    def send_session_message(
        self,
        destination: str,
        message_text: str
    ) -> Tuple[bool, str]:
        """
        Send a session message (free-form text within 24-hour window)
        
        Args:
            destination: Recipient phone number
            message_text: Message content
            
        Returns:
            Tuple of (success, message_id or error)
        """
        destination = self._normalize_phone(destination)
        
        payload = {
            "source": self.source_number,
            "destination": destination,
            "message": json.dumps({
                "type": "text",
                "text": message_text
            }),
            "src.name": self.app_name
        }
        
        try:
            logger.info(f"Sending session message to {destination}")
            
            response = requests.post(
                f"{self.api_url}/msg",
                headers=self.headers,
                data=payload,
                timeout=30
            )
            
            result = response.json()
            
            if response.status_code in [200, 201, 202]:
                message_id = result.get("messageId", "")
                logger.info(f"Session message sent successfully. Message ID: {message_id}")
                return True, message_id
            else:
                error_msg = result.get("message", str(result))
                logger.error(f"Gupshup API error: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Error sending session message: {str(e)}")
            return False, str(e)


# Global client instance
gupshup_client = GupshupClient()


def send_otp(phone: str, otp_code: str) -> Tuple[bool, str]:
    """
    Send OTP via WhatsApp using Gupshup
    
    Args:
        phone: Recipient phone number
        otp_code: The OTP code to send
        
    Returns:
        Tuple of (success, message_id or error)
    """
    # For sandbox/testing, use session message if template not approved
    if not GUPSHUP_API_KEY:
        logger.warning("Gupshup API key not configured - OTP not sent")
        return False, "Gupshup not configured"
    
    # Try template message first
    success, result = gupshup_client.send_template_message(
        destination=phone,
        template_id=TEMPLATE_OTP,
        params=[otp_code]
    )
    
    if not success and "template" in result.lower():
        # Template not approved, try session message (for testing)
        logger.info("Template not available, sending as session message")
        message = f"Your Drops Curated verification code is {otp_code}. Valid for 10 minutes. Do not share this code."
        success, result = gupshup_client.send_session_message(phone, message)
    
    return success, result


def send_price_drop_alert(
    phone: str,
    product_name: str,
    new_price: str,
    old_price: str
) -> Tuple[bool, str]:
    """
    Send price drop alert via WhatsApp
    
    Args:
        phone: Recipient phone number
        product_name: Name of the product
        new_price: Current price
        old_price: Previous price
        
    Returns:
        Tuple of (success, message_id or error)
    """
    if not GUPSHUP_API_KEY:
        logger.warning("Gupshup API key not configured - alert not sent")
        return False, "Gupshup not configured"
    
    # Try template message first
    success, result = gupshup_client.send_template_message(
        destination=phone,
        template_id=TEMPLATE_PRICE_DROP,
        params=[product_name, new_price, old_price]
    )
    
    if not success and "template" in result.lower():
        # Template not approved, try session message
        message = f"Price Drop Alert! {product_name} is now Rs.{new_price} (was Rs.{old_price}). Shop now on Drops Curated!"
        success, result = gupshup_client.send_session_message(phone, message)
    
    return success, result


def send_new_drop_alert(
    phone: str,
    product_name: str,
    price: str,
    brand: str = ""
) -> Tuple[bool, str]:
    """
    Send new product drop alert via WhatsApp
    
    Args:
        phone: Recipient phone number
        product_name: Name of the product
        price: Product price
        brand: Brand name (optional)
        
    Returns:
        Tuple of (success, message_id or error)
    """
    if not GUPSHUP_API_KEY:
        logger.warning("Gupshup API key not configured - alert not sent")
        return False, "Gupshup not configured"
    
    # Try template message first
    success, result = gupshup_client.send_template_message(
        destination=phone,
        template_id=TEMPLATE_NEW_DROP,
        params=[product_name, price]
    )
    
    if not success and "template" in result.lower():
        # Template not approved, try session message
        brand_text = f" by {brand}" if brand else ""
        message = f"New Drop Alert! {product_name}{brand_text} just landed at Rs.{price}. Limited stock - shop now on Drops Curated!"
        success, result = gupshup_client.send_session_message(phone, message)
    
    return success, result


def send_bulk_alerts(
    phone_numbers: list,
    alert_type: str,
    alert_data: dict
) -> Dict[str, Any]:
    """
    Send alerts to multiple users
    
    Args:
        phone_numbers: List of recipient phone numbers
        alert_type: Type of alert ('price_drop', 'new_drop')
        alert_data: Alert data parameters
        
    Returns:
        Dictionary with success/failure counts
    """
    results = {
        "total": len(phone_numbers),
        "successful": 0,
        "failed": 0,
        "details": []
    }
    
    for phone in phone_numbers:
        if alert_type == "price_drop":
            success, msg_id = send_price_drop_alert(
                phone,
                alert_data.get("product_name", ""),
                alert_data.get("new_price", ""),
                alert_data.get("old_price", "")
            )
        elif alert_type == "new_drop":
            success, msg_id = send_new_drop_alert(
                phone,
                alert_data.get("product_name", ""),
                alert_data.get("price", ""),
                alert_data.get("brand", "")
            )
        else:
            success, msg_id = False, "Unknown alert type"
        
        if success:
            results["successful"] += 1
            results["details"].append({
                "phone": phone,
                "status": "sent",
                "message_id": msg_id
            })
        else:
            results["failed"] += 1
            results["details"].append({
                "phone": phone,
                "status": "failed",
                "error": msg_id
            })
    
    logger.info(f"Bulk alert complete: {results['successful']} sent, {results['failed']} failed")
    return results
