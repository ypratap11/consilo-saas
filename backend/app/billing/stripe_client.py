"""
Stripe Integration Client

Handles subscription creation, payment processing, and customer management.
"""

import os
import stripe
from typing import Dict, Optional, List
from fastapi import HTTPException


class StripeClient:
    """
    Wrapper for Stripe API operations.
    
    Handles subscriptions, payments, and customer management.
    """
    
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        
        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable is required")
        
        stripe.api_key = self.api_key
        
        # Price IDs for each plan (from Stripe dashboard)
        self.price_ids = {
            "starter": os.getenv("STRIPE_PRICE_STARTER"),
            "growth": os.getenv("STRIPE_PRICE_GROWTH"),
            "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE")
        }
    
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> stripe.Customer:
        """
        Create a new Stripe customer.
        
        Args:
            email: Customer email
            name: Customer full name
            metadata: Additional metadata (e.g., tenant_id, user_id)
            
        Returns:
            Stripe Customer object
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return customer
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create Stripe customer: {str(e)}"
            )
    
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict] = None,
        trial_days: int = 0
    ) -> stripe.checkout.Session:
        """
        Create a Stripe Checkout session for subscription.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for the plan
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if user cancels
            metadata: Additional metadata
            trial_days: Number of trial days (0 = no trial)
            
        Returns:
            Stripe Checkout Session
        """
        try:
            session_params = {
                "customer": customer_id,
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": price_id,
                    "quantity": 1
                }],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata or {}
            }
            
            # Add trial if specified
            if trial_days > 0:
                session_params["subscription_data"] = {
                    "trial_period_days": trial_days
                }
            
            session = stripe.checkout.Session.create(**session_params)
            return session
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create checkout session: {str(e)}"
            )
    
    def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> stripe.billing_portal.Session:
        """
        Create a Stripe billing portal session.
        
        Customers can manage subscription, payment methods, invoices.
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session
            
        Returns:
            Billing portal session
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create billing portal: {str(e)}"
            )
    
    def get_subscription(self, subscription_id: str) -> stripe.Subscription:
        """Get subscription details"""
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve subscription: {str(e)}"
            )
    
    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> stripe.Subscription:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of current period
            
        Returns:
            Updated subscription
        """
        try:
            if at_period_end:
                return stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                return stripe.Subscription.delete(subscription_id)
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cancel subscription: {str(e)}"
            )
    
    def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_behavior: str = "create_prorations"
    ) -> stripe.Subscription:
        """
        Update subscription to a different plan.
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New price ID to switch to
            proration_behavior: How to handle proration (create_prorations/none)
            
        Returns:
            Updated subscription
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription['items']['data'][0].id,
                    "price": new_price_id
                }],
                proration_behavior=proration_behavior
            )
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update subscription: {str(e)}"
            )
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> stripe.Event:
        """
        Verify Stripe webhook signature.
        
        Args:
            payload: Raw request body
            signature: Stripe-Signature header value
            
        Returns:
            Verified Stripe Event
            
        Raises:
            HTTPException: If signature invalid
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
            return event
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=400,
                detail="Invalid signature"
            )
    
    def get_upcoming_invoice(self, customer_id: str) -> Optional[stripe.Invoice]:
        """Get upcoming invoice for customer"""
        try:
            return stripe.Invoice.upcoming(customer=customer_id)
        except stripe.error.InvalidRequestError:
            # No upcoming invoice (not on subscription)
            return None
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get upcoming invoice: {str(e)}"
            )
    
    def list_payment_methods(self, customer_id: str) -> List[stripe.PaymentMethod]:
        """List payment methods for customer"""
        try:
            methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            return methods.data
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list payment methods: {str(e)}"
            )


# Singleton instance
stripe_client = StripeClient()
