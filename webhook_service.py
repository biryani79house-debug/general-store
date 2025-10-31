#!/usr/bin/env python3
"""
Simple Webhook Service for Kirana Store Order Notifications
This service receives order notifications from the main FastAPI app
and can send WhatsApp messages or perform other actions.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import requests
from dotenv import load_dotenv
import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Kirana Store Webhook Service",
    description="Receives order notifications and sends WhatsApp messages",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
WHATSAPP_WEBHOOK_SECRET = os.getenv('WHATSAPP_WEBHOOK_SECRET', 'your-webhook-secret-here')
WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL', '')  # Your WhatsApp API endpoint
WHATSAPP_API_KEY = os.getenv('WHATSAPP_API_KEY', '')  # Your WhatsApp API key

# Twilio WhatsApp Configuration (set in Railway environment variables for security)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', '')

# Use Twilio if credentials are available, otherwise fallback to browser method
USE_TWILIO = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_NUMBER)

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

class OrderData:
    def __init__(self, data: Dict[str, Any]):
        self.customer_name = data.get('customer_name', 'Customer')
        self.phone_number = data.get('phone_number', '')
        self.items = data.get('items', [])
        self.total_bill = data.get('total_bill', 0)
        self.order_id = data.get('order_id', 'N/A')

    def format_order_message(self) -> str:
        """Format order confirmation message for WhatsApp"""
        items_text = "\n".join([f"• {item['quantity']}x {item['product_name']}" for item in self.items])

        message = f"""🙏 *Thank you {self.customer_name} for your order!*

📦 *Order Received:*
{items_text}

💰 *Total Amount: ₹{self.total_bill:.2f}*

📱 *Customer: {self.customer_name}*
📞 *Phone: {self.phone_number}*

✅ *Order confirmed and being prepared!*
🚚 *Delivery within 30-60 minutes*

🏪 *Thank you for choosing Raza Wholesale and Retail!* 🛒"""

        return message

def send_whatsapp_message(phone_number: str, message: str) -> bool:
    """
    Send WhatsApp message using Twilio API (if credentials available) or browser fallback
    """
    # Try Twilio first if credentials are available
    if USE_TWILIO:
        return send_whatsapp_via_twilio(phone_number, message)
    else:
        # Fallback to browser method
        return send_whatsapp_via_browser(phone_number, message)

def send_whatsapp_via_twilio(phone_number: str, message: str) -> bool:
    """
    Send WhatsApp message using Twilio Business API (fully automated)
    """
    try:
        from twilio.rest import Client

        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Format phone number
        clean_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        if not clean_number.startswith('+'):
            clean_number = '+91' + clean_number

        # Send WhatsApp message
        twilio_message = client.messages.create(
            from_=f'whatsapp:{TWILIO_WHATSAPP_NUMBER}',
            body=message,
            to=f'whatsapp:{clean_number}'
        )

        logger.info(f"✅ WhatsApp message sent via Twilio to {clean_number}: {twilio_message.sid}")
        return True

    except ImportError:
        logger.error("❌ Twilio library not installed")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to send WhatsApp via Twilio: {str(e)}")
        return False

def send_whatsapp_via_browser(phone_number: str, message: str) -> bool:
    """
    Send WhatsApp message using direct WhatsApp URL (fallback method)
    Opens WhatsApp in default browser with pre-filled message
    """
    try:
        # Format phone number (remove any non-numeric characters except +)
        clean_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        if not clean_number.startswith('+'):
            clean_number = '+91' + clean_number  # Add Indian country code if missing

        # Create WhatsApp URL with pre-filled message
        whatsapp_url = f"https://wa.me/{clean_number}?text={requests.utils.quote(message)}"

        # Try to open WhatsApp URL in default browser
        import webbrowser
        import subprocess
        import platform

        try:
            if platform.system() == "Windows":
                # On Windows, use start command to open URL
                subprocess.run(["cmd", "/c", "start", whatsapp_url], check=True)
            else:
                # On other systems, use webbrowser
                webbrowser.open(whatsapp_url)

            logger.info(f"✅ WhatsApp URL opened for {phone_number}: {whatsapp_url}")
            return True

        except Exception as browser_error:
            logger.error(f"❌ Failed to open WhatsApp URL in browser: {str(browser_error)}")
            return False

    except Exception as e:
        logger.error(f"❌ Error in send_whatsapp_via_browser: {str(e)}")
        return False

@app.post("/webhook/order-notification")
async def receive_order_notification(request: Request):
    """
    Receive order notifications from the main FastAPI app
    """
    try:
        # Temporarily disable authorization for debugging
        # Verify webhook secret if provided
        # if WHATSAPP_WEBHOOK_SECRET:
        #     auth_header = request.headers.get('Authorization', '')
        #     if not auth_header.startswith('Bearer ') or auth_header.split(' ')[1] != WHATSAPP_WEBHOOK_SECRET:
        #         logger.warning("Unauthorized webhook attempt")
        #         raise HTTPException(status_code=401, detail="Unauthorized")

        # Get order data
        order_data = await request.json()
        logger.info(f"📦 Received order notification: {json.dumps(order_data, indent=2)}")

        # Parse order data
        order = OrderData(order_data)

        # Format WhatsApp message
        whatsapp_message = order.format_order_message()

        # Send WhatsApp message
        success = send_whatsapp_message(order.phone_number, whatsapp_message)

        # Log the order
        log_entry = {
            "timestamp": datetime.now(IST).isoformat(),
            "order_id": order.order_id,
            "customer_name": order.customer_name,
            "phone_number": order.phone_number,
            "total_bill": order.total_bill,
            "items": order.items,
            "whatsapp_sent": success
        }

        # Save to log file
        with open('orders.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        return {
            "status": "success",
            "message": "Order notification received",
            "whatsapp_sent": success,
            "order_id": order.order_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    whatsapp_method = "twilio_whatsapp_api" if USE_TWILIO else "browser_whatsapp_fallback"

    return {
        "status": "healthy",
        "timestamp": datetime.now(IST).isoformat(),
        "whatsapp_method": whatsapp_method,
        "twilio_available": USE_TWILIO,
        "twilio_configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_NUMBER)
    }

@app.get("/orders")
async def get_recent_orders(limit: int = 10):
    """Get recent orders from log file"""
    try:
        orders = []
        if os.path.exists('orders.log'):
            with open('orders.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()[-limit:]  # Get last N orders
                for line in lines:
                    try:
                        orders.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue

        return {
            "orders": orders,
            "count": len(orders)
        }
    except Exception as e:
        logger.error(f"Error reading orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading orders: {str(e)}")

if __name__ == "__main__":
    # Use a simple approach without uvicorn's file watching
    import uvicorn

    port = int(os.environ.get("WEBHOOK_PORT", 8001))
    logger.info(f"🚀 Starting webhook service on port {port} (no file watching)")

    # Disable all file watching and reloading
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        reload_dirs=None,
        reload_includes=None,
        reload_excludes=None,
        reload_delay=None,
        log_level="info",
        access_log=False
    )
