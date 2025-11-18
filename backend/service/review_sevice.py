from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.customer import Customer
from backend.models.product import Product
from backend.models.review import Review
from backend.schemas.review import Review_read, Review_create, Review_update
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler

def reveiw_the_product(
    product_id: int,
    add_review: Review_create,
    db: Session,
    current_user: Customer
) -> Review_read:
    """
    Add a review for a product by the current user.
    """
    if not check_permission(current_user, "review_the_prduct"):
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Unauthorized action")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    new_review = Review(
        rating=add_review.rating,
        comment=add_review.comment,
        product_id=product_id,
        user_id=current_user.id
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return Review_read.from_orm(new_review)

def update_product_review(
    product_id: int,
    update_review: Review_update,
    db: Session,
    current_user: Customer
) -> Review_read:
    """
    Update an existing review for a product by the current user.
    """
    if not check_permission(current_user, "review_the_prduct"):
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Unauthorized action")

    review = db.query(Review).filter(
        Review.product_id == product_id,
        Review.user_id == current_user.id
    ).first()
    if not review:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Review not found")

    for key, value in update_review.dict(exclude_unset=True).items():
        setattr(review, key, value)

    db.commit()
    db.refresh(review)

    return Review_read.from_orm(review)

def get_reviews(
    product_id: int,
    db: Session,
    current_user: Customer
) -> list[Review_read]:
    """
    Retrieve all reviews for a specific product.
    """
    if not check_permission(current_user, "review_the_prduct"):
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Unauthorized action")

    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    if not reviews:
        raise error_handler(status.HTTP_404_NOT_FOUND, "No reviews found for this product")

    return [Review_read.from_orm(r) for r in reviews]

def review_delete_by_customer(
    review_id: int,
    db: Session,
    current_user: Customer
) -> dict:
    """
    Allow a customer to delete their own review.
    """
    if not check_permission(current_user, "delete_the_review"):
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Unauthorized action")

    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == current_user.id
    ).first()
    if not review:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Review not found")

    db.delete(review)
    db.commit()

    return {"message": "The review has been deleted successfully"}
