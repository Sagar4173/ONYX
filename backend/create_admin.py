"""
Create Initial Admin User for ONYX Platform
Run this script to create the first admin user after initial setup
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone
from dotenv import load_dotenv
from database import init_database, close_database
from models.user import User, UserRole, UserStatus
from services.auth.auth_service import auth_service


async def create_admin_user():
    """Create the initial admin user"""
    
    print("🔐 ONYX Platform - Initial Admin Setup")
    print("=" * 50)
    
    # Initialize database
    await init_database()
    
    # Check if any admin users exist
    admin_count = await User.find({"role": UserRole.ADMIN}).count()
    if admin_count > 0:
        print(f"❌ Admin user(s) already exist ({admin_count} found)")
        print("   If you need to create another admin, use the web interface")
        return
    
    # Get admin details
    print("Enter details for the initial admin user:")
    
    email = input("Email: ").strip()
    if not email:
        print("❌ Email is required")
        return
    
    username = input("Username: ").strip()
    if not username:
        print("❌ Username is required")
        return
    
    full_name = input("Full Name: ").strip()
    if not full_name:
        print("❌ Full name is required")
        return
    
    password = input("Password: ").strip()
    if not password:
        print("❌ Password is required")
        return
    
    organization = input("Organization (optional): ").strip() or None
    
    # Validate password strength
    try:
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('Password must contain at least one uppercase letter, lowercase letter, digit, and special character')
            
    except ValueError as e:
        print(f"❌ Password validation failed: {e}")
        return
    
    # Check if email/username already exists
    existing_email = await User.find_one({"email": email.lower()})
    if existing_email:
        print("❌ Email already exists")
        return
    
    existing_username = await User.find_one({"username": username.lower()})
    if existing_username:
        print("❌ Username already exists")
        return
    
    # Create admin user
    try:
        hashed_password = auth_service.hash_password(password)
        
        admin_user = User(
            email=email.lower(),
            username=username.lower(),
            full_name=full_name,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,  # Activate immediately
            organization=organization,
            is_email_verified=True,  # Skip email verification for admin
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        await admin_user.insert()
        
        print("\n✅ Admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   Username: {username}")
        print(f"   Role: {UserRole.ADMIN}")
        print(f"   Status: {UserStatus.ACTIVE}")
        print("\n🚀 You can now log in to the platform using these credentials.")
        
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        
    finally:
        await close_database()


async def list_users():
    """List all existing users"""
    print("👥 Current Users")
    print("=" * 50)
    
    await init_database()
    
    users = await User.find_all().to_list()
    
    if not users:
        print("No users found.")
    else:
        for user in users:
            print(f"📧 {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Name: {user.full_name}")
            print(f"   Role: {user.role}")
            print(f"   Status: {user.status}")
            print(f"   Created: {user.created_at}")
            print()
    
    await close_database()


async def reset_user_password():
    """Reset a user's password"""
    print("🔑 Reset User Password")
    print("=" * 50)
    
    await init_database()
    
    email_or_username = input("Enter email or username: ").strip()
    if not email_or_username:
        print("❌ Email or username is required")
        return
    
    user = await User.find_one({
        "$or": [
            {"email": email_or_username.lower()},
            {"username": email_or_username.lower()}
        ]
    })
    
    if not user:
        print("❌ User not found")
        return
    
    print(f"Found user: {user.full_name} ({user.email})")
    confirm = input("Reset password for this user? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Password reset cancelled")
        return
    
    new_password = input("New password: ").strip()
    if not new_password:
        print("❌ Password is required")
        return
    
    # Validate password
    try:
        if len(new_password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in new_password)
        has_lower = any(c.islower() for c in new_password)
        has_digit = any(c.isdigit() for c in new_password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in new_password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('Password must contain at least one uppercase letter, lowercase letter, digit, and special character')
            
    except ValueError as e:
        print(f"❌ Password validation failed: {e}")
        return
    
    # Update password
    try:
        user.hashed_password = auth_service.hash_password(new_password)
        user.last_password_change = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        
        # Reset failed attempts and unlock account
        user.failed_login_attempts = 0
        user.locked_until = None
        
        await user.save()
        
        print("✅ Password reset successfully!")
        
    except Exception as e:
        print(f"❌ Failed to reset password: {e}")
    
    finally:
        await close_database()


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            asyncio.run(list_users())
        elif command == "reset":
            asyncio.run(reset_user_password())
        elif command == "create":
            asyncio.run(create_admin_user())
        else:
            print("❌ Unknown command. Use: create, list, or reset")
    else:
        # Default action
        asyncio.run(create_admin_user())
