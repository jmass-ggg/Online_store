from fastapi import Depends, HTTPException, status, Security
from backend.database import get_db
from backend.utils.jwt import get_current_customer,get_current_seller

def check_permission(user,action:str):
    roles=user.role_name
    permission={
        "Admin": {  # Admin
            "delete_other_account":True,
            "delete_any_product": True,
            "verify_seller": True,
            "list_users": True,
            "change_user_role": True,
            "approved_application":True,
            
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
    role_permission=permission.get(roles,{})
    return role_permission.get(action,False)

def require_permission(action: str, get_user=Depends):
    """
    Dependency factory for permissions.
    Example:
        Depends(require_permission("delete_other_account", get_current_customer))
        Depends(require_permission("add_product", get_current_seller))
    """
    def dependency(current_user = Depends(get_user)):
        if not check_permission(current_user, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied for action: {action}"
            )
        return current_user
    return dependency