"""Stripe 支付：创建 Checkout 会话、处理 Webhook"""
import os
from datetime import datetime, timedelta
from typing import Optional

import stripe
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import User, get_db
from auth import get_current_user
from plans import PLANS

# 从环境变量读取（正式上线前填入真实 Key）
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_your_key_here")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_your_secret_here")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

router = APIRouter(prefix="/api/payment", tags=["payment"])


class CheckoutIn(BaseModel):
    plan: str        # "pro" or "annual"
    period: str      # "monthly" or "yearly"


@router.post("/checkout")
def create_checkout(
    body: CheckoutIn,
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    if body.plan not in ("pro", "annual"):
        raise HTTPException(status_code=400, detail="无效套餐")

    plan_cfg = PLANS[body.plan]
    price_key = f"stripe_price_{body.period}"
    price_id = plan_cfg.get(price_key, "")

    if not price_id:
        raise HTTPException(
            status_code=400,
            detail=f"Stripe Price ID 未配置，请在 plans.py 中填入 {price_key}"
        )

    # 获取或创建 Stripe Customer
    customer_id = user.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(email=user.email, metadata={"user_id": user.id})
        customer_id = customer.id
        user.stripe_customer_id = customer_id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/pricing",
        metadata={"user_id": user.id, "plan": body.plan},
    )
    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"].get("user_id")
        plan = session["metadata"].get("plan", "pro")
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.plan = plan
            # 订阅到期时间：月付30天，年付365天
            sub_id = session.get("subscription")
            if sub_id:
                sub = stripe.Subscription.retrieve(sub_id)
                user.sub_expires = datetime.fromtimestamp(sub["current_period_end"])
            else:
                user.sub_expires = datetime.utcnow() + timedelta(days=365)
            db.commit()

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        customer_id = sub["customer"]
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.plan = "free"
            user.sub_expires = None
            db.commit()

    elif event["type"] in ("invoice.payment_succeeded",):
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]
        sub_id = invoice.get("subscription")
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user and sub_id:
            sub = stripe.Subscription.retrieve(sub_id)
            user.sub_expires = datetime.fromtimestamp(sub["current_period_end"])
            db.commit()

    return {"received": True}


@router.get("/plans")
def get_plans():
    """返回前端展示用的套餐信息"""
    result = []
    for key, p in PLANS.items():
        result.append({
            "id": key,
            "name": p["name"],
            "price_monthly": p["price_monthly"],
            "price_yearly": p["price_yearly"],
            "daily_downloads": p["daily_downloads"],
            "max_quality": p["max_quality"],
            "features": p["features"],
            "limits": p.get("limits", []),
        })
    return result
