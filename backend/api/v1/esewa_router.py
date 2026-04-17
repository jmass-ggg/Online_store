from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from uuid import uuid4
import hmac
import html

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.core.error_handler import error_handler
from backend.database import get_db
from backend.models.order import Order, OrderStatus
from backend.models.payment import Payment, PaymentProvider, PaymentStatus
from backend.config.esewa_utils import (
    canonical_message,
    decode_esewa_data,
    hmac_sha256_base64,
)
from backend.core.settings_esewa import (
    ESEWA_FORM_URL,
    ESEWA_PRODUCT_CODE,
    ESEWA_SECRET_KEY,
    ESEWA_STATUS_URL,
)
from uuid import UUID
router = APIRouter(prefix="/payments/esewa", tags=["eSewa"])


FRONTEND_BASE_URL = "http://localhost:5173"


def money_str(amount: Decimal) -> str:
    s = f"{Decimal(str(amount)).quantize(Decimal('0.01')):f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def auto_submit_form(action_url: str, fields: Dict[str, str]) -> str:
    inputs = "\n".join(
        f'<input type="hidden" name="{html.escape(str(k))}" value="{html.escape(str(v))}"/>'
        for k, v in fields.items()
    )
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Redirecting to eSewa...</title>
  </head>
  <body>
    <p>Redirecting to eSewa...</p>
    <form id="f" action="{html.escape(action_url)}" method="POST">
      {inputs}
      <noscript>
        <button type="submit">Continue to eSewa</button>
      </noscript>
    </form>
    <script>
      document.getElementById("f").submit();
    </script>
  </body>
</html>""".strip()


def _safe_eq(a: str, b: str) -> bool:
    return hmac.compare_digest((a or "").encode("utf-8"), (b or "").encode("utf-8"))


def build_frontend_result_url(
    *,
    order_id: UUID,
    payment_status: str,
    esewa_status: str = "",
    ref_id: Optional[str] = None,
) -> str:
    params = {
        "order_id": order_id,
        "payment_status": payment_status,
        "esewa_status": esewa_status,
    }
    if ref_id:
        params["ref_id"] = ref_id

    return f"{FRONTEND_BASE_URL}/payment/esewa/result?{urlencode(params)}"


def _create_payment_attempt(db: Session, order: Order) -> Payment:
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
    return payment


async def status_check(
    *,
    product_code: str,
    total_amount: str,
    transaction_uuid: str,
) -> Dict[str, Any]:
    params = {
        "product_code": product_code,
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(ESEWA_STATUS_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"eSewa status API error: {exc}") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Unexpected response from eSewa status API")

    return data


def _apply_esewa_status(payment: Payment, status: str, ref_id: Optional[str]) -> None:
    s = (status or "").upper().strip()

    if s == "COMPLETE":
        payment.status = PaymentStatus.COMPLETE
        payment.ref_id = ref_id
        payment.verified_at = datetime.now(timezone.utc)
        payment.order.status = OrderStatus.COMPLETED
        return

    if s == "PENDING":
        payment.status = PaymentStatus.PENDING
        return

    if s == "AMBIGUOUS":
        payment.status = PaymentStatus.AMBIGUOUS
        return

    if s == "CANCELED":
        payment.status = PaymentStatus.FAILED
        payment.order.status = OrderStatus.CANCELLED
        return

    if s == "NOT_FOUND":
        payment.status = PaymentStatus.NOT_FOUND
        payment.order.status = OrderStatus.CANCELLED
        return

    if s == "FULL_REFUND":
        payment.status = PaymentStatus.FULL_REFUND
        return

    if s == "PARTIAL_REFUND":
        payment.status = PaymentStatus.PARTIAL_REFUND
        return

    payment.status = PaymentStatus.FAILED
    payment.order.status = OrderStatus.CANCELLED


def _mark_latest_order_payment_failed(db: Session, order_id: UUID) -> None:
    payment = (
        db.query(Payment)
        .filter(
            Payment.order_id == order_id,
            Payment.provider == PaymentProvider.ESEWA,
        )
        .order_by(Payment.id.desc())
        .first()
    )

    if payment:
        payment.status = PaymentStatus.FAILED
        if payment.order:
            payment.order.status = OrderStatus.CANCELLED
        db.commit()


@router.get("/initiate", response_class=HTMLResponse)
def initiate(order_id: UUID, request: Request, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise error_handler(404, "Order not found")

    payment = _create_payment_attempt(db, order)

    amount = Decimal(str(order.total_price)).quantize(Decimal("0.01"))
    tax_amount = Decimal("0.00")
    product_service_charge = Decimal("0.00")
    product_delivery_charge = Decimal("0.00")
    total_amount = (
        amount + tax_amount + product_service_charge + product_delivery_charge
    ).quantize(Decimal("0.01"))

    success_url = f"{request.url_for('esewa_success')}?order_id={order.id}"
    failure_url = f"{request.url_for('esewa_failure')}?order_id={order.id}"

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

    message = canonical_message(fields, signed_field_names)
    fields["signature"] = hmac_sha256_base64(message, ESEWA_SECRET_KEY)

    return auto_submit_form(ESEWA_FORM_URL, fields)


@router.api_route("/success", name="esewa_success")
async def success(request: Request, db: Session = Depends(get_db)):
    order_id_from_query = request.query_params.get("order_id")

    data = request.query_params.get("data")
    if not data and request.method == "POST":
        form = await request.form()
        data = form.get("data")

    if not data:
        if order_id_from_query and order_id_from_query.isdigit():
            return RedirectResponse(
                url=build_frontend_result_url(
                    order_id=UUID(order_id_from_query),
                    payment_status="FAILED",
                    esewa_status="FAILED",
                ),
                status_code=303,
            )
        raise error_handler(400, "Missing data")

    decoded = decode_esewa_data(data)
    if not isinstance(decoded, dict):
        raise error_handler(400, "Invalid data payload")

    signed_field_names = decoded.get("signed_field_names")
    received_sig = decoded.get("signature")

    if not signed_field_names or not received_sig:
        raise error_handler(400, "Missing signature fields")

    message = canonical_message(decoded, signed_field_names)
    computed_sig = hmac_sha256_base64(message, ESEWA_SECRET_KEY)

    if not _safe_eq(computed_sig, received_sig):
        raise HTTPException(status_code=400, detail="Invalid signature")

    tx_uuid = decoded.get("transaction_uuid")
    if not tx_uuid:
        raise HTTPException(status_code=400, detail="Missing transaction_uuid")

    payment: Optional[Payment] = (
        db.query(Payment)
        .filter(Payment.transaction_uuid == tx_uuid)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    product_code = str(decoded.get("product_code") or ESEWA_PRODUCT_CODE)
    total_amount = str(decoded.get("total_amount") or "").strip()
    if not total_amount:
        total_amount = money_str(Decimal(str(payment.amount)).quantize(Decimal("0.01")))

    status_response = await status_check(
        product_code=product_code,
        total_amount=total_amount,
        transaction_uuid=tx_uuid,
    )

    esewa_status = str(status_response.get("status") or "AMBIGUOUS").upper().strip()
    ref_id = status_response.get("ref_id")

    _apply_esewa_status(payment, esewa_status, ref_id)
    db.commit()
    db.refresh(payment)

    return RedirectResponse(
        url=build_frontend_result_url(
            order_id=payment.order_id,
            payment_status=str(payment.status),
            esewa_status=esewa_status,
            ref_id=ref_id,
        ),
        status_code=303,
    )



@router.api_route("/failure", name="esewa_failure")
def failure(request: Request, db: Session = Depends(get_db)):
    order_id = request.query_params.get("order_id")

    if order_id and order_id.isdigit():
        numeric_order_id = UUID(order_id)
        _mark_latest_order_payment_failed(db, numeric_order_id)

        return RedirectResponse(
            url=build_frontend_result_url(
                order_id=numeric_order_id,
                payment_status="FAILED",
                esewa_status="CANCELED",
            ),
            status_code=303,
        )

    return RedirectResponse(
        url=f"{FRONTEND_BASE_URL}/payment/esewa/result?payment_status=FAILED&esewa_status=CANCELED",
        status_code=303,
    )


@router.get("/poll/{order_id}")
async def poll(order_id: UUID, db: Session = Depends(get_db)):
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

    status_response = await status_check(
        product_code=ESEWA_PRODUCT_CODE,
        total_amount=total_amount,
        transaction_uuid=payment.transaction_uuid,
    )

    esewa_status = str(status_response.get("status") or "AMBIGUOUS").upper().strip()
    ref_id = status_response.get("ref_id")

    _apply_esewa_status(payment, esewa_status, ref_id)
    db.commit()
    db.refresh(payment)

    return {
        "order_id": order_id,
        "payment_status": str(payment.status),
        "status": esewa_status,
        "ref_id": ref_id,
    }