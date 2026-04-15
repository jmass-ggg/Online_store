import hashlib
import secrets

def generate_email_token() -> str:
    return secrets.token_urlsafe(32)

def hash_email_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def send_seller_verification_email(email: str, token: str) -> None:
    verify_link = f"http://localhost:8000/seller/verify-email?token={token}"
    print("=" * 60)
    print(f"Send email to: {email}")
    print("Subject: Verify your seller account")
    print(f"Verification link: {verify_link}")
    print("=" * 60)
    
def send_customer_verification_email(email: str, token: str) -> None:
    verify_link = f"http://localhost:8000/user/verified-email?token={token}"
    print("=" * 60)
    print(f"Send email to: {email}")
    print("Subject: Verify your customer account")
    print(f"Verification link: {verify_link}")
    print("=" * 60)