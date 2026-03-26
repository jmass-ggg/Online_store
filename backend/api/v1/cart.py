from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.cart import CartOut, CartItemAdd, DecreaseQty
from backend.utils.jwt import get_current_customer
from backend.models.customer import Customer
from backend.models.cart import Cart
from backend.models.cart_items import CartItem
from backend.service.cart_service import (
    add_to_cart_by_customer,
    get_or_create_active_cart,
    uncart_the_product,
    decrease__item_quantity,
    clear_cart,
    
)
from backend.schemas.cart import (CartItemAdd,
    DecreaseQty,
    CartItemSelectIn,CartProductsOut,
    CartSelectionOut,CartItemOut,CartOut,ProductOnlyOut,ProductVariantOnlyOut,CartItemProductOut,ProductMiniOut,ProductVariantMiniOut,CartItemSelectIn,SelectedCartItemOut,CartSelectionOut
    )
from backend.models.ProductVariant import ProductVariant
from backend.models.product import Product
from sqlalchemy.orm import Session, selectinload,joinedload
from uuid import UUID
from backend.core.error_handler import error_handler

router = APIRouter(prefix="/cart", tags=["Cart"])


def to_cart_out(db:Session,cart: Cart) -> dict:
    loaded_cart=(
        db.query(Cart).filter(Cart.id == cart.id)
        .with_for_update()
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.variant)
            .selectinload(ProductVariant.product)
            
        ).first()
    )
    if not loaded_cart:
        raise error_handler(400, "Cart is empty")
    select_items=[item for item in loaded_cart.items if item.selected]
    subtotal=sum(
        (item.price* item.quantity  for item in select_items),Decimal("0.00")
    )
    seller_delivery_map={}
    for item in select_items:
        if not item.variant or not item.variant.product or not item.variant.product.seller:
            continue
        seller = item.variant.product.seller
        seller_id = str(seller.id)
        if seller_id not in seller_delivery_map:
            charge=(
                seller.delivery[0].delivery_charge
                if seller.delivery else Decimal("0.00")
            )
            seller_delivery_map[seller_id]=charge
    delivery_charge=sum(seller_delivery_map.values(),Decimal("0.00"))
    total=subtotal+delivery_charge
        
        
    return {
        "cart_id": str(loaded_cart.id),
        "buyer_id": str(loaded_cart.buyer_id),
        "status": loaded_cart.status,

        "selected_count": len(select_items),
        "subtotal": float(subtotal),
        "delivery_charge": float(delivery_charge),
        "total": float(total),

        "delivery_breakdown": [
            {
                "seller_id": seller_id,
                "delivery_charge": float(charge),
            }
            for seller_id, charge in seller_delivery_map.items()
        ],


        "items": [
            {
                "cart_item_id": str(item.id),
                "quantity": item.quantity,
                "price": float(item.price),
                "line_total": float(item.price * item.quantity),
                "selected": item.selected,

                "product_variant": {
                    "variant_id": str(item.variant.id),
                    "sku": item.variant.sku,
                    "color": item.variant.color,
                    "size": item.variant.size,
                    "price": float(item.variant.price),
                    "stock_quantity": item.variant.stock_quantity,
                    "is_active": item.variant.is_active,
                } if item.variant else None,

                "product": {
                    "product_id": str(item.variant.product.id),
                    "product_name": item.variant.product.product_name,
                    "url_slug": item.variant.product.url_slug,
                    "product_category": item.variant.product.product_category.value
                        if item.variant.product.product_category else None,
                    "target_audience": item.variant.product.target_audience.value
                        if item.variant.product.target_audience else None,
                    "description": item.variant.product.description,
                    "image_url": item.variant.product.image_url,
                    "status": item.variant.product.status.value
                        if item.variant.product.status else None,
                    "seller_id": str(item.variant.product.seller.id)
                        if item.variant.product.seller else None,
                } if item.variant and item.variant.product else None,
            }
            for item in loaded_cart.items
        ]
    }
from decimal import Decimal
from fastapi import APIRouter, Depends, status

def serialize_cart(cart: Cart) -> CartOut:
    subtotal = sum((item.price * item.quantity for item in cart.items), Decimal("0.00"))

    return CartOut(
        id=cart.id,
        buyer_id=cart.buyer_id,
        status=cart.status,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
        subtotal=subtotal,
        items=[
            CartItemOut(
                id=item.id,
                cart_id=item.cart_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                price=item.price,
            )
            for item in cart.items
        ],
    )
    
@router.get("/me")
def get_my_cart(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    cart = get_or_create_active_cart(db, buyer_id=current_customer.id)
    return to_cart_out(db, cart)

@router.post("/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    payload: CartItemAdd,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    cart = add_to_cart_by_customer(
        db=db,
        buyer_id=current_customer.id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
    )
    return serialize_cart(cart)


@router.patch("/items/{item_id}/decrease", response_model=CartProductsOut)
def item_quantity_delete(
    item_id: UUID,
    payload: DecreaseQty,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    cart = decrease__item_quantity(item_id, payload, db, current_customer.id)
    return to_cart_out(db, cart)


@router.delete("/items/{item_id}", response_model=CartProductsOut)
def remove_cart_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    cart = uncart_the_product(db=db, buyer_id=current_customer.id, item_id=item_id)
    return to_cart_out(db, cart)


@router.delete("/all-item/delete", response_model=CartProductsOut)
def delete_all_item(
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_customer),
):
    cart = clear_cart(db, current_user.id)
    return to_cart_out(db, cart)