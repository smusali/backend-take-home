#!/usr/bin/env python3
"""
User creation script for creating attorney accounts.

This script allows administrators to create new attorney users
from the command line with custom credentials.

Usage:
    python scripts/create_user.py <username> <email> <password>
    
Example:
    python scripts/create_user.py attorney1 attorney1@firm.com SecurePass123
    
Environment:
    Requires .env file with database configuration.
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.security import hash_password
from app.db.database import get_db_context
from app.db.repositories.user_repository import UserRepository
from app.models.user import User


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Password must be at least 8 characters long and contain:
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format.
    
    Username must be 3-50 characters and contain only
    alphanumeric characters, underscores, and hyphens.
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must not exceed 50 characters"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    return True, ""


def create_user(username: str, email: str, password: str) -> None:
    """
    Create a new attorney user account.
    
    Args:
        username: Unique username for the account
        email: Unique email address
        password: Plain text password (will be hashed)
        
    Raises:
        ValueError: If validation fails or user already exists
    """
    is_valid, error = validate_username(username)
    if not is_valid:
        raise ValueError(f"Invalid username: {error}")
    
    if not validate_email(email):
        raise ValueError(f"Invalid email format: {email}")
    
    is_valid, error = validate_password(password)
    if not is_valid:
        raise ValueError(f"Invalid password: {error}")
    
    print("=" * 60)
    print("Creating New Attorney User")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Email:    {email}")
    print("-" * 60)
    
    try:
        with get_db_context() as db:
            user_repo = UserRepository(User, db)
            
            existing_user = user_repo.get_by_username(username)
            if existing_user:
                raise ValueError(f"User with username '{username}' already exists")
            
            existing_email = user_repo.get_by_email(email)
            if existing_email:
                raise ValueError(f"User with email '{email}' already exists")
            
            hashed_password = hash_password(password)
            
            user = user_repo.create({
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "is_active": True
            })
            
            print("✅ User created successfully!")
            print(f"User ID: {user.id}")
            print("=" * 60)
            
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Database error: {e}")


def print_usage():
    """Print usage instructions."""
    print("\nUsage:")
    print("  python scripts/create_user.py <username> <email> <password>")
    print("\nExample:")
    print("  python scripts/create_user.py attorney1 attorney1@firm.com SecurePass123")
    print("\nRequirements:")
    print("  - Username: 3-50 characters, alphanumeric with _ or -")
    print("  - Email: Valid email format")
    print("  - Password: Min 8 chars, must include uppercase, lowercase, and digit")
    print()


def main():
    """Main entry point for the user creation script."""
    if len(sys.argv) != 4:
        print("❌ Error: Invalid number of arguments")
        print_usage()
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    try:
        create_user(username, email, password)
    except ValueError as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  User creation interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
