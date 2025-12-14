#!/usr/bin/env python3
"""
Database seeding script to create initial admin user.

This script creates a default attorney user account for accessing
the internal dashboard. The credentials are printed to console
after successful creation.

Usage:
    python scripts/seed_db.py
    
Environment:
    Requires .env file with database configuration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.security import hash_password
from app.db.database import get_db_context
from app.db.repositories.user_repository import UserRepository
from app.models.user import User


DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL = "admin@leadmanagement.local"
DEFAULT_PASSWORD = "Admin123!SecurePassword"


def seed_admin_user() -> None:
    """
    Create initial admin user in the database.
    
    If admin user already exists, the script will skip creation
    and inform the user.
    """
    print("=" * 60)
    print("Database Seeding - Creating Admin User")
    print("=" * 60)
    
    try:
        with get_db_context() as db:
            user_repo = UserRepository(User, db)
            
            existing_user = user_repo.get_by_username(DEFAULT_USERNAME)
            if existing_user:
                print(f"\n⚠️  Admin user '{DEFAULT_USERNAME}' already exists.")
                print("Skipping user creation.\n")
                return
            
            existing_email = user_repo.get_by_email(DEFAULT_EMAIL)
            if existing_email:
                print(f"\n⚠️  User with email '{DEFAULT_EMAIL}' already exists.")
                print("Skipping user creation.\n")
                return
            
            hashed_password = hash_password(DEFAULT_PASSWORD)
            
            admin_user = user_repo.create({
                "username": DEFAULT_USERNAME,
                "email": DEFAULT_EMAIL,
                "hashed_password": hashed_password,
                "is_active": True
            })
            
            print("\n✅ Admin user created successfully!")
            print("\n" + "-" * 60)
            print("Default Admin Credentials:")
            print("-" * 60)
            print(f"Username: {DEFAULT_USERNAME}")
            print(f"Email:    {DEFAULT_EMAIL}")
            print(f"Password: {DEFAULT_PASSWORD}")
            print("-" * 60)
            print("\n⚠️  IMPORTANT: Change the default password after first login!")
            print("\n" + "=" * 60)
            
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        sys.exit(1)


def main():
    """Main entry point for the seed script."""
    try:
        seed_admin_user()
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
