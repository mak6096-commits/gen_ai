import os
import hmac
import hashlib
from fastapi import HTTPException, Request, Header
from app.models import PaymentWebhook, OrderStatus
from app.crud import OrderCRUD
from typing import Optional


class WebhookHandler:
    """Handle payment webhooks with HMAC verification"""
    
    def __init__(self):
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", "your-webhook-secret-key")
        self.processed_events = set()  # Simple replay protection
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature"""
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        return hmac.compare_digest(expected_signature, signature)
    
    def is_replay(self, event_id: str) -> bool:
        """Check if event was already processed (simple replay protection)"""
        if event_id in self.processed_events:
            return True
        self.processed_events.add(event_id)
        return False
    
    async def process_payment_webhook(
        self, 
        request: Request,
        x_webhook_signature: Optional[str] = Header(None)
    ):
        """Process payment webhook with signature verification"""
        
        # Get raw body
        body = await request.body()
        
        # Verify signature
        if not x_webhook_signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        
        if not self.verify_signature(body, x_webhook_signature):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")
        
        # Parse webhook data
        try:
            webhook_data = PaymentWebhook.parse_raw(body)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid webhook payload: {str(e)}")
        
        # Simple replay protection using payment_id as event_id
        event_id = f"{webhook_data.event_type}_{webhook_data.payment_id}_{webhook_data.order_id}"
        if self.is_replay(event_id):
            return {"status": "ignored", "reason": "duplicate_event"}
        
        # Process payment success
        if webhook_data.event_type == "payment.succeeded":
            try:
                # Update order status to PAID
                order = OrderCRUD.get_order(webhook_data.order_id)
                
                if order.status != OrderStatus.PENDING:
                    return {
                        "status": "ignored", 
                        "reason": f"Order status is {order.status}, expected PENDING"
                    }
                
                # Update order to PAID status
                from app.models import OrderUpdate
                OrderCRUD.update_order(webhook_data.order_id, OrderUpdate(status=OrderStatus.PAID))
                
                return {
                    "status": "processed",
                    "order_id": webhook_data.order_id,
                    "new_status": "PAID"
                }
                
            except HTTPException as e:
                # Re-raise HTTP exceptions
                raise e
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")
        
        # Handle other event types
        return {"status": "ignored", "reason": f"Unhandled event type: {webhook_data.event_type}"}


# Global webhook handler instance
webhook_handler = WebhookHandler()
