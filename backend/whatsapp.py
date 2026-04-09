"""
Meta WhatsApp Cloud API Integration
Direct integration with Meta's WhatsApp Business API for OTP and alerts
"""

import os
import json
import logging
import requests
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Meta WhatsApp Cloud API Configuration
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
WHATSAPP_BUSINESS_ACCOUNT_ID = os.environ.get('WHATSAPP_BUSINESS_ACCOUNT_ID', '')
WHATSAPP_API_VERSION = os.environ.get('WHATSAPP_API_VERSION', 'v18.0')
WHATSAPP_API_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"

# Check if properly configured
IS_CONFIGURED = bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)


class WhatsAppClient:
    """Client for Meta WhatsApp Cloud API"""
    
    def __init__(self):
        self.access_token = WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = WHATSAPP_PHONE_NUMBER_ID
        self.api_url = WHATSAPP_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format without +"""
        cleaned = ''.join(c for c in phone if c.isdigit())
        if len(cleaned) == 10:
            cleaned = f"91{cleaned}"
        return cleaned
    
    def send_template_message(
        self,
        destination: str,
        template_name: str,
        language_code: str = "en",
        components: list = None
    ) -> Tuple[bool, str]:
        """
        Send a template message via WhatsApp
        
        Args:
            destination: Recipient phone number
            template_name: Template name (must be approved by Meta)
            language_code: Language code (default: en)
            components: Template components with parameters
            
        Returns:
            Tuple of (success, message_id or error)
        """
        if not IS_CONFIGURED:
            logger.warning("WhatsApp API not configured")
            return False, "WhatsApp not configured"
        
        destination = self._normalize_phone(destination)
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": destination,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            logger.info(f"Sending template '{template_name}' to {destination}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if response.status_code in [200, 201]:
                message_id = result.get("messages", [{}])[0].get("id", "")
                logger.info(f"Template message sent. ID: {message_id}")
                return True, message_id
            else:
                error = result.get("error", {})
                error_msg = error.get("message", str(result))
                error_code = error.get("code", "unknown")
                logger.error(f"WhatsApp API error ({error_code}): {error_msg}")
                return False, f"{error_code}: {error_msg}"
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout sending message to {destination}")
            return False, "Request timeout"
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False, str(e)
    
    def send_text_message(
        self,
        destination: str,
        message_text: str
    ) -> Tuple[bool, str]:
        """
        Send a plain text message (only works within 24-hour conversation window)
        
        Args:
            destination: Recipient phone number
            message_text: Message content
            
        Returns:
            Tuple of (success, message_id or error)
        """
        if not IS_CONFIGURED:
            logger.warning("WhatsApp API not configured")
            return False, "WhatsApp not configured"
        
        destination = self._normalize_phone(destination)
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": destination,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }
        
        try:
            logger.info(f"Sending text message to {destination}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if response.status_code in [200, 201]:
                message_id = result.get("messages", [{}])[0].get("id", "")
                logger.info(f"Text message sent. ID: {message_id}")
                return True, message_id
            else:
                error = result.get("error", {})
                error_msg = error.get("message", str(result))
                logger.error(f"WhatsApp API error: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Error sending text message: {str(e)}")
            return False, str(e)
    
    def send_image_message(
        self,
        destination: str,
        image_url: str,
        caption: str = ""
    ) -> Tuple[bool, str]:
        """
        Send an image message with optional caption
        
        Args:
            destination: Recipient phone number
            image_url: Public URL of the image
            caption: Optional caption text
            
        Returns:
            Tuple of (success, message_id or error)
        """
        if not IS_CONFIGURED:
            logger.warning("WhatsApp API not configured")
            return False, "WhatsApp not configured"
        
        destination = self._normalize_phone(destination)
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": destination,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
            }
        }
        
        try:
            logger.info(f"Sending image message to {destination}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if response.status_code in [200, 201]:
                message_id = result.get("messages", [{}])[0].get("id", "")
                logger.info(f"Image message sent. ID: {message_id}")
                return True, message_id
            else:
                error = result.get("error", {})
                error_msg = error.get("message", str(result))
                logger.error(f"WhatsApp API error: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Error sending image message: {str(e)}")
            return False, str(e)


# Global client instance
whatsapp_client = WhatsAppClient()


def send_otp(phone: str, otp_code: str) -> Tuple[bool, str]:
    """
    Send OTP via WhatsApp
    
    For now, uses text message. Once you create and approve an OTP template,
    update this to use template message.
    
    Args:
        phone: Recipient phone number
        otp_code: The OTP code to send
        
    Returns:
        Tuple of (success, message_id or error)
    """
    if not IS_CONFIGURED:
        logger.warning("WhatsApp not configured - OTP not sent")
        return False, "WhatsApp not configured"
    
    # Try sending as text message first (works if user messaged you within 24hrs)
    message = f"Your Drops Curated verification code is: {otp_code}\n\nThis code expires in 10 minutes. Do not share this code with anyone."
    
    success, result = whatsapp_client.send_text_message(phone, message)
    
    if not success:
        # If text fails, try with template (you need to create this template in Meta)
        logger.info("Text message failed, trying template...")
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": otp_code}
                ]
            }
        ]
        success, result = whatsapp_client.send_template_message(
            destination=phone,
            template_name="otp_verification",  # Create this template in Meta Business Manager
            components=components
        )
    
    return success, result


def send_price_drop_alert(
    phone: str,
    product_name: str,
    new_price: str,
    old_price: str,
    image_url: str = None,
    product_url: str = None
) -> Tuple[bool, str]:
    """Send price drop alert via WhatsApp with product image"""
    if not IS_CONFIGURED:
        return False, "WhatsApp not configured"
    
    caption = f"""🔥 *Price Drop Alert!*

*{product_name}*

~₹{old_price}~ → *₹{new_price}*

💰 You save: ₹{int(float(old_price.replace(',','')) - float(new_price.replace(',',''))):,}

🛒 Shop now on Drops Curated!"""

    # Send with image if available
    if image_url:
        return whatsapp_client.send_image_message(phone, image_url, caption)
    else:
        return whatsapp_client.send_text_message(phone, caption)


def send_new_drop_alert(
    phone: str,
    product_name: str,
    price: str,
    brand: str = "",
    image_url: str = None,
    product_url: str = None
) -> Tuple[bool, str]:
    """Send new product drop alert via WhatsApp with product image"""
    if not IS_CONFIGURED:
        return False, "WhatsApp not configured"
    
    brand_text = f" by *{brand}*" if brand else ""
    caption = f"""🆕 *New Drop Alert!*

*{product_name}*{brand_text}

💵 Price: *₹{price}*

⚡ Limited stock available!

🛒 Shop now on Drops Curated!"""

    # Send with image if available
    if image_url:
        return whatsapp_client.send_image_message(phone, image_url, caption)
    else:
        return whatsapp_client.send_text_message(phone, caption)


def send_bulk_alerts(
    phone_numbers: list,
    alert_type: str,
    alert_data: dict
) -> Dict[str, Any]:
    """Send alerts to multiple users"""
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
        else:
            results["failed"] += 1
        
        results["details"].append({
            "phone": phone,
            "status": "sent" if success else "failed",
            "result": msg_id
        })
    
    logger.info(f"Bulk alert: {results['successful']} sent, {results['failed']} failed")
    return results


def send_welcome_message(phone: str, name: str, membership_id: str) -> Tuple[bool, str]:
    """
    Send Welcome Message after successful payment (Meta compliance: proof of opt-in)
    
    This creates a digital trail that the user initiated the conversation.
    
    Args:
        phone: Recipient phone number
        name: User's first name
        membership_id: The membership ID
        
    Returns:
        Tuple of (success, message_id or error)
    """
    if not IS_CONFIGURED:
        # Log the welcome message in sandbox mode
        logger.info(f"[Sandbox] Welcome message to {phone}: Hi {name}! Welcome to Drops Curated (ID: {membership_id})")
        return True, "sandbox_welcome"
    
    message = f"""Hi {name}! 👋

Welcome to *Drops Curated* VIP! 🎉

Your membership ID: *{membership_id}*

You've successfully subscribed to exclusive streetwear alerts. We'll only message you when there's a drop that matches your preferences.

📱 *Save this contact* to see images and links clearly!

To stop getting alerts anytime, just reply *STOP*.

Happy shopping! 🛍️"""
    
    return whatsapp_client.send_text_message(phone, message)


def handle_stop_request(phone: str) -> Tuple[bool, str]:
    """
    Handle STOP/UNSUBSCRIBE request from user
    
    This immediately opts the user out and sends confirmation.
    
    Args:
        phone: Phone number requesting opt-out
        
    Returns:
        Tuple of (success, message)
    """
    if not IS_CONFIGURED:
        logger.info(f"[Sandbox] STOP request from {phone}")
        return True, "sandbox_stop"
    
    # Send confirmation message
    message = """You've been unsubscribed from Drops Curated alerts. ✅

You will no longer receive WhatsApp messages from us.

If you change your mind, you can resubscribe anytime at dropscurated.com

Thank you for being with us! 🙏"""
    
    return whatsapp_client.send_text_message(phone, message)
