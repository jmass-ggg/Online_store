from __future__ import annotations

from fastapi import Depends, HTTPException, status

from backend.models.seller import Seller
from backend.utils.jwt import get_current_seller


def verify_email_seller_or_not(
    seller: Seller = Depends(get_current_seller),
) -> Seller:
    if not seller.user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller email not verified",
        )
    return seller


def verify_seller_or_not(
    seller: Seller = Depends(get_current_seller),
) -> Seller:
    if seller.status == "REJECTED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller rejected",
        )

    if not seller.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller account not approved",
        )

    if not seller.user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller email not verified",
        )

    return seller