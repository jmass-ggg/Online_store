from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from backend.core.error_handler import error_handler
from backend.database import get_db
from backend.models.order import Order, OrderStatus
from backend.models.payment import Payment, PaymentStatus, PaymentProvider
from backend.config.esewa_utils import canonical_message, hmac_sha256_base64, decode_esewa_data
from backend.core.settings_esewa import (
    ESEWA_SECRET_KEY, ESEWA_PRODUCT_CODE, ESEWA_FORM_URL, ESEWA_STATUS_URL
)

router = APIRouter(prefix="/payments/esewa", tags=["eSewa"])

def money_str(amount:Decimal)->str:
    return f"{amount:.2f}"

def auto_submit_form(action_url: str, fields: dict) -> str:
    inputs = "\n".join([f'<input type="hidden" name="{k}" value="{v}"/>' for k, v in fields.items()])
    return f"""
<!doctype html>
<html>
  <body>
    <form id="f" action="{action_url}" method="POST">
      {inputs}
    </form>
    <script>document.getElementById("f").submit();</script>
  </body>
</html>
""".strip()

@router.get("/initiate", response_class=HTMLResponse)
def initiate(order_id: int, db: Session = Depends(get_db)):
    order=db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise error_handler(404,"order not found")
    payment=db.query(Payment).filter(Payment.order_id == order_id,Payment.provider == PaymentProvider.ESEWA).order_by(Payment.id.desc()).first()
    if not payment:
        payment = Payment(
            order_id=order.id,
            provider=PaymentProvider.ESEWA,
            status=PaymentStatus.PENDING,
            amount=order.total_price,
            transaction_uuid=str(uuid4()),
            initiated_at=datetime.now(timezone.utc),
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
    signed_field_names = "total_amount,transaction_uuid,product_code"
    amount=order.total_price
    tax_amount=Decimal("0.00")
    product_service_charge=Decimal("0.00")
    product_delivery_charge = Decimal("0.00")
    total_amount=amount+tax_amount+product_delivery_charge
    fields = {
        "amount": money_str(amount),
        "tax_amount": money_str(tax_amount),
        "total_amount": money_str(total_amount),
        "transaction_uuid": payment.transaction_uuid,
        "product_code": ESEWA_PRODUCT_CODE,
        "product_service_charge": money_str(product_service_charge),
        "product_delivery_charge": money_str(product_delivery_charge),
        "success_url": "https://YOUR-DOMAIN.COM/payments/esewa/success",
        "failure_url": "https://YOUR-DOMAIN.COM/payments/esewa/failure",
        "signed_field_names": signed_field_names,
    }
    msg=canonical_message(fields,signed_field_names)
    fields["signed_field_names"]=hmac_sha256_base64(msg,ESEWA_SECRET_KEY)
    return auto_submit_form(ESEWA_FORM_URL,fields)

async def status_check(product_code:str,total_amount:str,transaction_uuid:str):
    params={
        "total_amount":total_amount,
        "product_code":product_code,
        "transaction_uuid":transaction_uuid
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r=await client.get(ESEWA_FORM_URL,params=params)
        r.raise_for_status()
        return r.json()