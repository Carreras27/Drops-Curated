"""
Meta WhatsApp Cloud API Integration
Direct integration with Meta's WhatsApp Business API for OTP and alerts
Includes rate limiting and opt-out handling for Meta compliance
"""

import os
import json
import logging
import requests
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

# Meta WhatsApp Cloud API Configuration
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
WHATSAPP_BUSINESS_ACCOUNT_ID = os.environ.get('WHATSAPP_BUSINESS_ACCOUNT_ID', '')
WHATSAPP_API_VERSION = os.environ.get('WHATSAPP_API_VERSION', 'v18.0')
WHATSAPP_API_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"

# Check if properly configured
IS_CONFIGURED = bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)

# ============ RATE LIMITING ============
# Rate limits per user per day (to control WhatsApp costs)
RATE_LIMITS = {
    'instant': 10,      # Max 10 instant alerts per day per user
    'digest': 1,        # 1 daily digest
    'otp': 5,           # Max 5 OTP requests per day
    'total_daily': 15   # Total max messages per user per day
}

# In-memory rate tracking (use Redis in production)
_rate_tracker: Dict[str, Dict] = defaultdict(lambda: {
    'instant': 0,
    'digest': 0,
    'otp': 0,
    'total': 0,
    'reset_at': None
})

def _get_rate_key(phone: str) -> str:
    """Get rate limit key for a phone number"""
    return phone.replace('+', '').replace(' ', '')

def _reset_rate_if_needed(phone: str):
    """Reset rate limits if a new day has started"""
    key = _get_rate_key(phone)
    tracker = _rate_tracker[key]
    
    now = datetime.now(timezone.utc)
    if tracker['reset_at'] is None or now >= tracker['reset_at']:
        # Reset for new day
        tracker['instant'] = 0
        tracker['digest'] = 0
        tracker['otp'] = 0
        tracker['total'] = 0
        tracker['reset_at'] = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

def check_rate_limit(phone: str, message_type: str = 'instant') -> Tuple[bool, str]:
    """
    Check if user is within rate limits
    
    Args:
        phone: User's phone number
        message_type: 'instant', 'digest', or 'otp'
        
    Returns:
        Tuple of (allowed, reason)
    """
    key = _get_rate_key(phone)
    _reset_rate_if_needed(phone)
    
    tracker = _rate_tracker[key]
    
    # Check total daily limit
    if tracker['total'] >= RATE_LIMITS['total_daily']:
        return False, f"Daily message limit reached ({RATE_LIMITS['total_daily']})"
    
    # Check type-specific limit
    if message_type in RATE_LIMITS and tracker[message_type] >= RATE_LIMITS[message_type]:
        return False, f"{message_type.title()} limit reached ({RATE_LIMITS[message_type]}/day)"
    
    return True, "OK"

def record_message_sent(phone: str, message_type: str = 'instant'):
    """Record that a message was sent for rate limiting"""
    key = _get_rate_key(phone)
    _reset_rate_if_needed(phone)
    
    tracker = _rate_tracker[key]
    if message_type in tracker:
        tracker[message_type] += 1
    tracker['total'] += 1

def get_rate_status(phone: str) -> Dict:
    """Get current rate limit status for a user"""
    key = _get_rate_key(phone)
    _reset_rate_if_needed(phone)
    
    tracker = _rate_tracker[key]
    return {
        'instant_remaining': RATE_LIMITS['instant'] - tracker['instant'],
        'otp_remaining': RATE_LIMITS['otp'] - tracker['otp'],
        'total_remaining': RATE_LIMITS['total_daily'] - tracker['total'],
        'reset_at': tracker['reset_at'].isoformat() if tracker['reset_at'] else None
    }

# ============ OPT-OUT MANAGEMENT ============
# In-memory opt-out list (use database in production)
_opted_out_users: set = set()

def is_opted_out(phone: str) -> bool:
    """Check if user has opted out"""
    key = _get_rate_key(phone)
    return key in _opted_out_users

def add_opt_out(phone: str):
    """Add user to opt-out list"""
    key = _get_rate_key(phone)
    _opted_out_users.add(key)
    logger.info(f"User {phone} opted out of WhatsApp messages")

def remove_opt_out(phone: str):
    """Remove user from opt-out list (when they resubscribe)"""
    key = _get_rate_key(phone)
    _opted_out_users.discard(key)
    logger.info(f"User {phone} removed from opt-out list")

async def sync_opt_outs_from_db(db):
    """Sync opt-out list from database on startup"""
    global _opted_out_users
    try:
        opted_out = await db.subscribers.find(
            {'whatsapp_opted_out': True}, 
            {'phone': 1, '_id': 0}
        ).to_list(10000)
        
        for sub in opted_out:
            _opted_out_users.add(_get_rate_key(sub['phone']))
        
        logger.info(f"Loaded {len(_opted_out_users)} opted-out users from database")
    except Exception as e:
        logger.error(f"Error syncing opt-outs: {e}")


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
    Send OTP via WhatsApp with rate limiting
    """
    # Check rate limit for OTP
    allowed, reason = check_rate_limit(phone, 'otp')
    if not allowed:
        logger.warning(f"OTP rate limit exceeded for {phone}: {reason}")
        return False, f"Rate limit exceeded: {reason}"
    
    if not IS_CONFIGURED:
        logger.warning("WhatsApp not configured - OTP not sent")
        record_message_sent(phone, 'otp')  # Still count for rate limiting
        return False, "WhatsApp not configured"
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
    """Send price drop alert via WhatsApp with rate limiting and opt-out check"""
    # Check opt-out
    if is_opted_out(phone):
        logger.info(f"User {phone} has opted out, skipping alert")
        return False, "User opted out"
    
    # Check rate limit
    allowed, reason = check_rate_limit(phone, 'instant')
    if not allowed:
        logger.warning(f"Rate limit exceeded for {phone}: {reason}")
        return False, f"Rate limit: {reason}"
    
    if not IS_CONFIGURED:
        logger.info(f"[Sandbox] Price drop alert to {phone}: {product_name} ₹{old_price} → ₹{new_price}")
        record_message_sent(phone, 'instant')
        return True, "sandbox_mode"
    
    caption = f"""🔥 *Price Drop Alert!*

*{product_name}*

~₹{old_price}~ → *₹{new_price}*

💰 You save: ₹{int(float(old_price.replace(',','')) - float(new_price.replace(',',''))):,}

🛒 Shop now on Drops Curated!

Reply STOP to unsubscribe."""

    # Send with image if available
    if image_url:
        success, result = whatsapp_client.send_image_message(phone, image_url, caption)
    else:
        success, result = whatsapp_client.send_text_message(phone, caption)
    
    if success:
        record_message_sent(phone, 'instant')
    
    return success, result


def send_new_drop_alert(
    phone: str,
    product_name: str,
    price: str,
    brand: str = "",
    image_url: str = None,
    product_url: str = None
) -> Tuple[bool, str]:
    """Send new product drop alert via WhatsApp with rate limiting and opt-out check"""
    # Check opt-out
    if is_opted_out(phone):
        logger.info(f"User {phone} has opted out, skipping alert")
        return False, "User opted out"
    
    # Check rate limit
    allowed, reason = check_rate_limit(phone, 'instant')
    if not allowed:
        logger.warning(f"Rate limit exceeded for {phone}: {reason}")
        return False, f"Rate limit: {reason}"
    
    if not IS_CONFIGURED:
        logger.info(f"[Sandbox] New drop alert to {phone}: {product_name} at ₹{price}")
        record_message_sent(phone, 'instant')
        return True, "sandbox_mode"
    
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
