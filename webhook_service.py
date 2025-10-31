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
    Send WhatsApp message using your preferred WhatsApp API service
    Replace this with your actual WhatsApp messaging service integration
    """
    try:
        # Example integration with a generic WhatsApp API
        # Replace with your actual WhatsApp service (Twilio, 360Dialog, etc.)

        if not WHATSAPP_API_URL or not WHATSAPP_API_KEY:
            logger.warning("WhatsApp API not configured - logging message instead")
            logger.info(f"WHATSAPP MESSAGE TO {phone_number}: {message}")
            return False

        # Example payload for a generic WhatsApp API
        payload = {
            "to": phone_number,
            "message": message,
            "api_key": WHATSAPP_API_KEY
        }

        response = requests.post(
            WHATSAPP_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            logger.info(f"✅ WhatsApp message sent successfully to {phone_number}")
            return True
        else:
            logger.error(f"❌ Failed to send WhatsApp message: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp message: {str(e)}")
        return False

@app.post("/webhook/order-notification")
async def receive_order_notification(request: Request):
    """
    Receive order notifications from the main FastAPI app
    """
    try:
        # Verify webhook secret if provided
        if WHATSAPP_WEBHOOK_SECRET:
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer ') or auth_header.split(' ')[1] != WHATSAPP_WEBHOOK_SECRET:
                logger.warning("Unauthorized webhook attempt")
                raise HTTPException(status_code=401, detail="Unauthorized")

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
    return {
        "status": "healthy",
        "timestamp": datetime.now(IST).isoformat(),
        "whatsapp_api_configured": bool(WHATSAPP_API_URL and WHATSAPP_API_KEY)
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
    import uvicorn

    port = int(os.environ.get("WEBHOOK_PORT", 8001))
    logger.info(f"🚀 Starting webhook service on port {port}")

    uvicorn.run(
        "webhook_service:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
