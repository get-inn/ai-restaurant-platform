"""
Initialize test database with required data for bot tests.
"""
import os
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, UUID, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid
from datetime import datetime

# Create custom models that match the database schema
Base = declarative_base()

class Account(Base):
    __tablename__ = "account"
    __table_args__ = {'schema': 'getinn_ops'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

class Restaurant(Base):
    __tablename__ = "restaurant"
    __table_args__ = {'schema': 'getinn_ops'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey('getinn_ops.account.id'), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

class UserProfile(Base):
    __tablename__ = "user_profile"
    __table_args__ = {'schema': 'getinn_ops'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey('getinn_ops.account.id'), nullable=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey('getinn_ops.restaurant.id'), nullable=True)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'))

# Connect to database
db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/restaurant")
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("Initializing test data...")
    
    # Create test account with fixed ID
    test_account_id = "00000000-0000-0000-0000-000000000001"
    test_account = db.query(Account).filter(Account.id == uuid.UUID(test_account_id)).first()
    if not test_account:
        print(f"Creating test account with id {test_account_id}")
        test_account = Account(
            id=uuid.UUID(test_account_id),
            name="Test Account"
        )
        db.add(test_account)
        db.commit()
        db.refresh(test_account)
    else:
        print(f"Test account {test_account_id} already exists")
    
    # Create test restaurant with fixed ID
    test_restaurant_id = "00000000-0000-0000-0000-000000000002"
    test_restaurant = db.query(Restaurant).filter(Restaurant.id == uuid.UUID(test_restaurant_id)).first()
    if not test_restaurant:
        print(f"Creating test restaurant with id {test_restaurant_id}")
        test_restaurant = Restaurant(
            id=uuid.UUID(test_restaurant_id),
            account_id=uuid.UUID(test_account_id),
            name="Test Restaurant"
        )
        db.add(test_restaurant)
        db.commit()
        db.refresh(test_restaurant)
    else:
        print(f"Test restaurant {test_restaurant_id} already exists")
    
    # Create predefined users with fixed IDs
    predefined_users = [
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000000"),
            "role": "admin",
            "account_id": None,
            "restaurant_id": None
        },
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
            "role": "admin",
            "account_id": uuid.UUID(test_account_id),
            "restaurant_id": None
        },
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
            "role": "account_manager",
            "account_id": uuid.UUID(test_account_id),
            "restaurant_id": None
        },
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
            "role": "restaurant_manager",
            "account_id": uuid.UUID(test_account_id),
            "restaurant_id": uuid.UUID(test_restaurant_id)
        },
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000004"),
            "role": "chef",
            "account_id": uuid.UUID(test_account_id),
            "restaurant_id": uuid.UUID(test_restaurant_id)
        }
    ]
    
    # Create or update user profiles
    for user_data in predefined_users:
        user_id = user_data["id"]
        user_profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        
        if not user_profile:
            print(f"Creating user profile for user {user_id}")
            user_profile = UserProfile(
                id=user_id,
                role=user_data["role"],
                account_id=user_data["account_id"],
                restaurant_id=user_data["restaurant_id"]
            )
            db.add(user_profile)
        else:
            print(f"User profile {user_id} already exists")
    
    # Commit user profile changes
    db.commit()
    
    # Check if users were created
    users = db.query(UserProfile).all()
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"  ID: {user.id}, Role: {user.role}")
    
    # Check if accounts were created
    accounts = db.query(Account).all()
    print(f"Found {len(accounts)} accounts:")
    for account in accounts:
        print(f"  ID: {account.id}, Name: {account.name}")
        
    # Check if restaurants were created
    restaurants = db.query(Restaurant).all()
    print(f"Found {len(restaurants)} restaurants:")
    for restaurant in restaurants:
        print(f"  ID: {restaurant.id}, Name: {restaurant.name}, Account ID: {restaurant.account_id}")
        
    print("Database initialization complete")
    
except Exception as e:
    print(f"Error initializing database: {e}")
    db.rollback()
finally:
    db.close()
