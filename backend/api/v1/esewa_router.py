from __future__ import annotations

from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
import hmac
import html

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.core.error_handler import error_handler
from backend.database import get_db
from backend.models.order import Order, OrderStatus
from backend.models.payment import Payment, PaymentStatus, PaymentProvider
from backend.config.esewa_utils import canonical_message, hmac_sha256_base64, decode_esewa_data
from backend.core.settings_esewa import (
    ESEWA_SECRET_KEY,
    ESEWA_PRODUCT_CODE,
    ESEWA_FORM_URL,    # ePay v2 form endpoint (rc/prod)
    ESEWA_STATUS_URL,  # ePay v2 status endpoint (uat/prod)
)

router = APIRouter(prefix="/payments/esewa", tags=["eSewa"])


# -----------------------
# helpers
# -----------------------
def money_str(amount: Decimal) -> str:
    return f"{amount:.2f}"


def auto_submit_form(action_url: str, fields: Dict[str, str]) -> str:
    # escape values to keep HTML safe
    inputs = "\n".join(
        f'<input type="hidden" name="{html.escape(str(k))}" value="{html.escape(str(v))}"/>'
        for k, v in fields.items()
    )
    return f"""<!doctype html>
<html>
  <body>
    <form id="f" action="{html.escape(action_url)}" method="POST">
      {inputs}
    </form>
    <script>document.getElementById("f").submit();</script>
  </body>
</html>""".strip()


def _safe_eq(a: str, b: str) -> bool:
    return hmac.compare_digest((a or "").encode("utf-8"), (b or "").encode("utf-8"))


def _get_or_create_pending_payment(db: Session, order: Order) -> Payment:
    """
    Use latest PENDING/AMBIGUOUS payment if exists, else create a new one.
    This prevents reusing an old COMPLETE/FAILED payment when user retries.
    """
    payment: Optional[Payment] = (
        db.query(Payment)
        .filter(
            Payment.order_id == order.id,
            Payment.provider == PaymentProvider.ESEWA,
        )
        .order_by(Payment.id.desc())
        .first()
    )

    if payment and payment.status in {PaymentStatus.PENDING, PaymentStatus.AMBIGUOUS}:
        # keep amount synced with latest order total
        payment.amount = order.total_price
        db.commit()
        db.refresh(payment)
        return payment

    payment = Payment(
        order_id=order.id,
        provider=PaymentProvider.ESEWA,
        status=PaymentStatus.PENDING,
        amount=order.total_price,  # store full total that user will pay
        transaction_uuid=str(uuid4()),
        initiated_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


async def status_check(*, product_code: str, total_amount: str, transaction_uuid: str) -> Dict[str, Any]:
 
    params = {
        "total_amount": total_amount,
        "product_code": product_code,
        "transaction_uuid": transaction_uuid,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(ESEWA_STATUS_URL, params=params)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            raise HTTPException(502, "Unexpected response from eSewa status API")
        return data


def _apply_esewa_status(payment: Payment, status: str, ref_id: Optional[str]) -> None:

    s = (status or "").upper().strip()

    if s == "COMPLETE":
        payment.status = PaymentStatus.COMPLETE
        payment.ref_id = ref_id
        payment.verified_at = datetime.now(timezone.utc)
        payment.order.status = OrderStatus.COMPLETED
        return

    if s in {"PENDING", "AMBIGUOUS"}:
        payment.status = PaymentStatus.AMBIGUOUS if s == "AMBIGUOUS" else PaymentStatus.PENDING
        return

    if s == "CANCELED":
        payment.status = PaymentStatus.NOT_FOUND
        payment.order.status = OrderStatus.CANCELLED
        return

    if s in {"FULL_REFUND", "PARTIAL_REFUND"}:
        payment.status = PaymentStatus.FULL_REFUND if s == "FULL_REFUND" else PaymentStatus.PARTIAL_REFUND
        return

    payment.status = PaymentStatus.FAILED
    payment.order.status = OrderStatus.CANCELLED

@router.get("/initiate", response_class=HTMLResponse)
def initiate(order_id: int, request: Request, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise error_handler(404, "Order not found")

    payment = _get_or_create_pending_payment(db, order)

    amount = Decimal(str(order.total_price)).quantize(Decimal("0.01"))
    tax_amount = Decimal("0.00")
    product_service_charge = Decimal("0.00")
    product_delivery_charge = Decimal("0.00")
    total_amount = (amount + tax_amount + product_service_charge + product_delivery_charge).quantize(Decimal("0.01"))

    success_url = str(request.url_for("esewa_success"))
    failure_url = str(request.url_for("esewa_failure"))

    signed_field_names = "total_amount,transaction_uuid,product_code"

    fields: Dict[str, str] = {
        "amount": money_str(amount),
        "tax_amount": money_str(tax_amount),
        "total_amount": money_str(total_amount),
        "transaction_uuid": payment.transaction_uuid,
        "product_code": ESEWA_PRODUCT_CODE,
        "product_service_charge": money_str(product_service_charge),
        "product_delivery_charge": money_str(product_delivery_charge),
        "success_url": success_url,
        "failure_url": failure_url,
        "signed_field_names": signed_field_names,
    }

    msg = canonical_message(fields, signed_field_names)
    fields["signature"] = hmac_sha256_base64(msg, ESEWA_SECRET_KEY)

    return auto_submit_form(ESEWA_FORM_URL, fields)


@router.api_route("/success", methods=["GET", "POST"], name="esewa_success")
async def success(request: Request, db: Session = Depends(get_db)):

    data = request.query_params.get("data")
    if not data and request.method == "POST":
        form = await request.form()
        data = form.get("data")

    if not data:
        raise error_handler(400, "Missing data")

    decoded = decode_esewa_data(data)
    if not isinstance(decoded, dict):
        raise error_handler(400, "Invalid data payload")

    signed_field_names = decoded.get("signed_field_names")
    received_sig = decoded.get("signature")

    if not signed_field_names or not received_sig:
        raise error_handler(400, "Missing signature fields")

    msg = canonical_message(decoded, signed_field_names)
    computed_sig = hmac_sha256_base64(msg, ESEWA_SECRET_KEY)

    if not _safe_eq(computed_sig, received_sig):
        raise HTTPException(400, "Invalid signature")

    tx_uuid = decoded.get("transaction_uuid")
    if not tx_uuid:
        raise HTTPException(400, "Missing transaction_uuid")

    payment: Optional[Payment] = db.query(Payment).filter(Payment.transaction_uuid == tx_uuid).first()
    if not payment:
        raise HTTPException(404, "Payment not found")


    product_code = str(decoded.get("product_code") or "")
    total_amount = str(decoded.get("total_amount") or "")
    if not total_amount:
       
        total_amount = money_str(Decimal(str(payment.amount)).quantize(Decimal("0.01")))

    st = await status_check(
        product_code=product_code,
        total_amount=total_amount,
        transaction_uuid=tx_uuid,
    )

    st_status = str(st.get("status") or "AMBIGUOUS")
    st_ref_id = st.get("ref_id")

    _apply_esewa_status(payment, st_status, st_ref_id)
    db.commit()

    return {
        "ok": True,
        "order_id": payment.order_id,
        "payment_status": str(payment.status),
        "esewa_status": st_status,
        "ref_id": st_ref_id,
    }


@router.api_route("/failure", methods=["GET", "POST"], name="esewa_failure")
async def failure(request: Request, db: Session = Depends(get_db)):
    return {"ok": False, "message": "Payment failed or cancelled"}


@router.get("/poll/{order_id}")
async def poll(order_id: int, db: Session = Depends(get_db)):
    payment: Optional[Payment] = (
        db.query(Payment)
        .filter(
            Payment.order_id == order_id,
            Payment.provider == PaymentProvider.ESEWA,
        )
        .order_by(Payment.id.desc())
        .first()
    )
    if not payment:
        raise error_handler(404, "Payment not found")

    total_amount = money_str(Decimal(str(payment.amount)).quantize(Decimal("0.01")))
    st = await status_check(
        product_code=ESEWA_PRODUCT_CODE,
        total_amount=total_amount,
        transaction_uuid=payment.transaction_uuid,
    )
    return {"order_id": order_id, "status": st.get("status"), "ref_id": st.get("ref_id")}