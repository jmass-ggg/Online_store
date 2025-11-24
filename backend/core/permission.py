from fastapi import Depends, HTTPException, status, Security
from backend.database import get_db
from backend.utils.auth import auth2_schema

def check_permission(user,action:str):
    role=user.role_name
    permission={
        "Admin": {  # Admin
            "delete_other_account":True,
            "delete_any_product": True,
            "verify_seller": True,
            "list_users": True,
            "change_user_role": True,
            "approved_application":True
        },
        "Customer": 
        {  # Customer
            "browse_products": True,
            "place_order": True,
            "view_own_orders": True,
            "review_the_product":True,
            "delete_the_review":True
        },
        "Seller": {  # Seller
            "add_product": True,
            "edit_own_product": True,
            "delete_own_product": True,
            "view_own_orders": True,
            "view_orders":True
        }
    }
    role_permission=permission.get(role,{})
    return role_permission.get(action,False)
