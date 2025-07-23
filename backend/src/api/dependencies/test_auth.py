"""
Authentication dependencies for testing purposes.
These versions of the auth dependencies allow for bypassing authentication in test environments.
"""
from fastapi import Depends
from uuid import uuid4

async def get_test_user():
    """
    Returns a mock user for testing purposes.
    This removes the need for authentication in test environments.
    """
    return {
        "id": uuid4(),
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": True,
        "role": "admin",
    }

def check_test_role(allowed_roles):
    """
    A test version of the role check that always passes.
    """
    async def _check_role():
        return await get_test_user()
    return _check_role