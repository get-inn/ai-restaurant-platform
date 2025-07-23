"""
Seed data script for the restaurant platform.
This script populates the database with test data for development and testing.
"""

import uuid
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from src.api.core.logging_config import get_logger
from src.api.models import (
    Account, Restaurant, Store, Supplier, UserProfile, 
    UnitCategory, Unit, UnitConversion, 
    InventoryItem, InventoryStock, ItemSpecificUnitConversion,
    Recipe, RecipeIngredient,
    Menu, MenuItem, MenuContainsMenuItem,
    StaffOnboarding, OnboardingStep
)

logger = get_logger("restaurant_api")

def seed_database(db: Session) -> None:
    """
    Seed the database with test data.
    
    Args:
        db: Database session
    """
    try:
        logger.info("Starting database seeding...")
        
        # Create test accounts
        accounts = create_accounts(db)
        
        # Create restaurants for each account
        restaurants = create_restaurants(db, accounts)
        
        # Create stores for each restaurant
        stores = create_stores(db, restaurants)
        
        # Create suppliers
        suppliers = create_suppliers(db, accounts)
        
        # Create users
        create_users(db, accounts, restaurants)
        
        # Create inventory items
        inventory_items = create_inventory_items(db, accounts)
        
        # Create inventory stock
        create_inventory_stocks(db, stores, inventory_items)
        
        # Create inventory item unit conversions
        create_inventory_item_units(db, inventory_items)
        
        # Create recipes
        recipes = create_recipes(db, accounts, inventory_items)
        
        # Create menus and menu items
        create_menus(db, restaurants, recipes)
        
        # Create staff onboarding data
        create_staff_onboardings(db, restaurants)
        
        logger.info("Database seeding complete")
    
    except Exception as e:
        logger.error(f"Error during database seeding: {str(e)}")
        db.rollback()
        raise


def create_accounts(db: Session) -> List[Account]:
    """Create test accounts"""
    logger.info("Creating test accounts...")
    
    accounts = []
    account_names = [
        "Fine Dining Group",
        "Casual Eats Inc.",
        "Fast Food Enterprises"
    ]
    
    for name in account_names:
        account = Account(
            name=name
        )
        db.add(account)
        accounts.append(account)
    
    db.commit()
    for account in accounts:
        db.refresh(account)
    
    return accounts


def create_restaurants(db: Session, accounts: List[Account]) -> List[Restaurant]:
    """Create test restaurants for each account"""
    logger.info("Creating test restaurants...")
    
    restaurants = []
    restaurant_data = [
        # Fine Dining Group
        ("Le Bistro", accounts[0].id),
        ("Gourmet Heights", accounts[0].id),
        # Casual Eats Inc.
        ("Family Table", accounts[1].id),
        ("Urban Plates", accounts[1].id),
        # Fast Food Enterprises
        ("Quick Bites", accounts[2].id),
        ("Express Eats", accounts[2].id),
    ]
    
    for name, account_id in restaurant_data:
        restaurant = Restaurant(
            name=name,
            account_id=account_id
        )
        db.add(restaurant)
        restaurants.append(restaurant)
    
    db.commit()
    for restaurant in restaurants:
        db.refresh(restaurant)
    
    return restaurants


def create_stores(db: Session, restaurants: List[Restaurant]) -> List[Store]:
    """Create test stores for each restaurant"""
    logger.info("Creating test stores...")
    
    stores = []
    
    # Create 1-2 stores per restaurant
    for restaurant in restaurants:
        # Main location
        main_store = Store(
            name=f"{restaurant.name} - Main",
            restaurant_id=restaurant.id
        )
        db.add(main_store)
        stores.append(main_store)
        
        # 50% chance of second location
        if random.random() > 0.5:
            second_store = Store(
                name=f"{restaurant.name} - Downtown",
                restaurant_id=restaurant.id
            )
            db.add(second_store)
            stores.append(second_store)
    
    db.commit()
    for store in stores:
        db.refresh(store)
    
    return stores


def create_suppliers(db: Session, accounts: List[Account]) -> List[Supplier]:
    """Create test suppliers"""
    logger.info("Creating test suppliers...")
    
    suppliers = []
    supplier_data = [
        # For all accounts
        ("Fresh Produce Co.", {
            "email": "orders@freshproduce.example",
            "phone": "555-123-4567",
            "address": "123 Farm Road, Harvest Valley"
        }),
        ("Quality Meats Inc.", {
            "email": "sales@qualitymeats.example",
            "phone": "555-234-5678",
            "address": "456 Butcher Lane, Meatville"
        }),
        ("Seafood Direct", {
            "email": "orders@seafooddirect.example",
            "phone": "555-345-6789",
            "address": "789 Harbor Drive, Port City"
        }),
        ("Bakery Supplies", {
            "email": "info@bakerysupplies.example",
            "phone": "555-456-7890",
            "address": "101 Flour Street, Breadtown"
        }),
        ("Beverage World", {
            "email": "sales@beverageworld.example",
            "phone": "555-567-8901",
            "address": "202 Drink Avenue, Sipville"
        })
    ]
    
    for name, contact_info in supplier_data:
        # Assign each supplier to a random account
        account = random.choice(accounts)
        
        supplier = Supplier(
            name=name,
            account_id=account.id,
            contact_info=contact_info
        )
        db.add(supplier)
        suppliers.append(supplier)
    
    db.commit()
    for supplier in suppliers:
        db.refresh(supplier)
    
    return suppliers


def create_users(db: Session, accounts: List[Account], restaurants: List[Restaurant]) -> None:
    """Create test users with various roles"""
    logger.info("Creating test users...")
    
    # Create one admin user
    admin = UserProfile(
        id=uuid.uuid4(),
        role="admin"
    )
    db.add(admin)
    
    # Create account managers (one per account)
    for account in accounts:
        account_manager = UserProfile(
            id=uuid.uuid4(),
            role="account_manager",
            account_id=account.id
        )
        db.add(account_manager)
    
    # Create restaurant managers and chefs (one of each per restaurant)
    for restaurant in restaurants:
        # Restaurant manager
        restaurant_manager = UserProfile(
            id=uuid.uuid4(),
            role="restaurant_manager",
            account_id=restaurant.account_id,
            restaurant_id=restaurant.id
        )
        db.add(restaurant_manager)
        
        # Chef
        chef = UserProfile(
            id=uuid.uuid4(),
            role="chef",
            account_id=restaurant.account_id,
            restaurant_id=restaurant.id
        )
        db.add(chef)
        
        # Staff (2-4 per restaurant)
        staff_count = random.randint(2, 4)
        for _ in range(staff_count):
            staff = UserProfile(
                id=uuid.uuid4(),
                role="staff",
                account_id=restaurant.account_id,
                restaurant_id=restaurant.id
            )
            db.add(staff)
    
    db.commit()


def create_inventory_items(db: Session, accounts: List[Account]) -> List[Dict[str, Any]]:
    """Create inventory items for each account"""
    logger.info("Creating inventory items...")
    
    # Get unit categories and units
    unit_categories = {category.name: category for category in db.query(UnitCategory).all()}
    units = {unit.name: unit for unit in db.query(Unit).all()}
    
    inventory_items_by_account = {}
    
    # Common inventory items for all accounts
    common_items = [
        # Produce
        ("Tomatoes", "Produce", "raw_ingredient", units["Kilogram"], Decimal("2.50")),
        ("Lettuce", "Produce", "raw_ingredient", units["Kilogram"], Decimal("1.75")),
        ("Onions", "Produce", "raw_ingredient", units["Kilogram"], Decimal("1.20")),
        ("Potatoes", "Produce", "raw_ingredient", units["Kilogram"], Decimal("1.00")),
        ("Carrots", "Produce", "raw_ingredient", units["Kilogram"], Decimal("1.30")),
        
        # Proteins
        ("Chicken Breast", "Meat", "raw_ingredient", units["Kilogram"], Decimal("8.50")),
        ("Ground Beef", "Meat", "raw_ingredient", units["Kilogram"], Decimal("9.00")),
        ("Salmon Fillet", "Seafood", "raw_ingredient", units["Kilogram"], Decimal("14.50")),
        ("Shrimp", "Seafood", "raw_ingredient", units["Kilogram"], Decimal("16.00")),
        
        # Dairy
        ("Milk", "Dairy", "raw_ingredient", units["Liter"], Decimal("1.20")),
        ("Butter", "Dairy", "raw_ingredient", units["Kilogram"], Decimal("7.50")),
        ("Cheese", "Dairy", "raw_ingredient", units["Kilogram"], Decimal("8.00")),
        ("Cream", "Dairy", "raw_ingredient", units["Liter"], Decimal("3.50")),
        
        # Grains
        ("Rice", "Grains", "raw_ingredient", units["Kilogram"], Decimal("2.00")),
        ("Pasta", "Grains", "raw_ingredient", units["Kilogram"], Decimal("1.80")),
        ("Flour", "Baking", "raw_ingredient", units["Kilogram"], Decimal("1.20")),
        
        # Beverages
        ("Soda", "Beverages", "raw_ingredient", units["Liter"], Decimal("1.50")),
        ("Coffee Beans", "Beverages", "raw_ingredient", units["Kilogram"], Decimal("15.00")),
        ("Tea", "Beverages", "raw_ingredient", units["Kilogram"], Decimal("20.00")),
        
        # Semi-finished products
        ("Tomato Sauce", "Sauces", "semi_finished", units["Liter"], Decimal("3.20")),
        ("Chicken Stock", "Sauces", "semi_finished", units["Liter"], Decimal("2.50")),
        ("Bread Rolls", "Bakery", "semi_finished", units["Dozen"], Decimal("4.50")),
        
        # Finished products
        ("Cheesecake", "Desserts", "finished_product", units["Piece"], Decimal("3.50")),
        ("Chocolate Cake", "Desserts", "finished_product", units["Piece"], Decimal("3.00")),
    ]
    
    for account in accounts:
        account_items = []
        
        for name, category, item_type, unit, cost in common_items:
            item = InventoryItem(
                account_id=account.id,
                name=name,
                description=f"{name} for culinary use",
                default_unit_id=unit.id,
                category=category,
                item_type=item_type,
                current_cost_per_unit=cost,
                reorder_level=Decimal("10.00") if item_type == "raw_ingredient" else Decimal("5.00")
            )
            db.add(item)
            account_items.append({
                "item": item, 
                "name": name, 
                "category": category,
                "item_type": item_type,
                "unit": unit,
                "cost": cost
            })
        
        inventory_items_by_account[str(account.id)] = account_items
    
    db.commit()
    
    # Refresh items
    for account_id, items in inventory_items_by_account.items():
        for item_dict in items:
            db.refresh(item_dict["item"])
    
    return inventory_items_by_account


def create_inventory_stocks(db: Session, stores: List[Store], inventory_items: Dict[str, List[Dict[str, Any]]]) -> None:
    """Create inventory stocks for each store"""
    logger.info("Creating inventory stocks...")
    
    for store in stores:
        # Get account ID for this store
        account_id = str(db.query(Restaurant.account_id).filter(Restaurant.id == store.restaurant_id).scalar())
        
        # Get inventory items for this account
        account_items = inventory_items.get(account_id, [])
        
        for item_dict in account_items:
            item = item_dict["item"]
            item_type = item_dict["item_type"]
            
            # Determine quantity based on item type
            if item_type == "raw_ingredient":
                quantity = Decimal(str(random.uniform(20.0, 100.0)))
            elif item_type == "semi_finished":
                quantity = Decimal(str(random.uniform(10.0, 50.0)))
            else:  # finished_product
                quantity = Decimal(str(random.uniform(5.0, 20.0)))
            
            # Round to 2 decimal places
            quantity = quantity.quantize(Decimal("0.01"))
            
            stock = InventoryStock(
                store_id=store.id,
                inventory_item_id=item.id,
                quantity=quantity,
                unit_id=item.default_unit_id,
                last_updated=datetime.now()
            )
            db.add(stock)
    
    db.commit()


def create_recipes(db: Session, accounts: List[Account], inventory_items: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Create recipes for each account"""
    logger.info("Creating recipes...")
    
    recipes_by_account = {}
    
    recipe_data = [
        ("Classic Burger", "Beef burger with lettuce, tomato, and onion", 
         [
             ("Ground Beef", 0.2),
             ("Tomatoes", 0.05),
             ("Lettuce", 0.03),
             ("Onions", 0.03),
             ("Bread Rolls", 1)
         ]),
        ("Grilled Salmon", "Fresh salmon fillet with vegetables",
         [
             ("Salmon Fillet", 0.2),
             ("Potatoes", 0.15),
             ("Carrots", 0.1),
             ("Butter", 0.02)
         ]),
        ("Caesar Salad", "Fresh salad with chicken and Caesar dressing",
         [
             ("Lettuce", 0.15),
             ("Chicken Breast", 0.1),
             ("Tomato Sauce", 0.05),
             ("Cheese", 0.03)
         ]),
        ("Pasta Carbonara", "Creamy pasta with cheese",
         [
             ("Pasta", 0.15),
             ("Cream", 0.1),
             ("Cheese", 0.05),
             ("Onions", 0.02)
         ]),
        ("Chocolate Cake Slice", "Rich chocolate dessert",
         [
             ("Flour", 0.05),
             ("Butter", 0.03),
             ("Milk", 0.1),
             ("Chocolate Cake", 0.1)
         ])
    ]
    
    # Units for the yield
    each_unit = db.query(Unit).filter(Unit.name == "Each").first()
    
    for account in accounts:
        account_recipes = []
        
        # Get the inventory items for this account
        account_items_list = inventory_items.get(str(account.id), [])
        account_items_dict = {item_dict["name"]: item_dict["item"] for item_dict in account_items_list}
        
        for name, description, ingredients in recipe_data:
            recipe = Recipe(
                account_id=account.id,
                name=name,
                description=description,
                instructions=f"Instructions for preparing {name}",
                yield_quantity=Decimal("1.00"),
                yield_unit_id=each_unit.id
            )
            db.add(recipe)
            db.flush()  # To get the recipe ID
            
            # Create recipe ingredients
            for ingredient_name, quantity in ingredients:
                if ingredient_name in account_items_dict:
                    ingredient_item = account_items_dict[ingredient_name]
                    
                    recipe_ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        inventory_item_id=ingredient_item.id,
                        quantity=Decimal(str(quantity)),
                        unit_id=ingredient_item.default_unit_id
                    )
                    db.add(recipe_ingredient)
            
            account_recipes.append({
                "recipe": recipe,
                "name": name,
                "description": description
            })
        
        recipes_by_account[str(account.id)] = account_recipes
    
    db.commit()
    
    # Refresh recipes
    for account_id, recipes in recipes_by_account.items():
        for recipe_dict in recipes:
            db.refresh(recipe_dict["recipe"])
    
    return recipes_by_account


def create_menus(db: Session, restaurants: List[Restaurant], recipes: Dict[str, List[Dict[str, Any]]]) -> None:
    """Create menus and menu items for each restaurant"""
    logger.info("Creating menus and menu items...")
    
    for restaurant in restaurants:
        # Get account ID for this restaurant
        account_id = str(restaurant.account_id)
        
        # Get recipes for this account
        account_recipes = recipes.get(account_id, [])
        if not account_recipes:
            continue
        
        # Create a main menu for the restaurant
        main_menu = Menu(
            restaurant_id=restaurant.id,
            name="Main Menu",
            description=f"Main menu for {restaurant.name}",
            is_active=True
        )
        db.add(main_menu)
        db.flush()
        
        # Create menu items from recipes
        menu_items = []
        for recipe_dict in account_recipes:
            recipe = recipe_dict["recipe"]
            
            # Calculate price (recipe cost * markup)
            cost = calculate_recipe_cost(db, recipe.id)
            markup = Decimal(str(random.uniform(2.5, 4.0)))  # 2.5x to 4x markup
            price = (cost * markup).quantize(Decimal("0.01"))
            
            menu_item = MenuItem(
                account_id=restaurant.account_id,
                name=recipe.name,
                description=recipe.description,
                base_price=price,
                category=get_category_for_recipe(recipe.name),
                recipe_id=recipe.id
            )
            db.add(menu_item)
            menu_items.append(menu_item)
        
        db.flush()
        
        # Add menu items to the menu
        for i, menu_item in enumerate(menu_items):
            menu_contains = MenuContainsMenuItem(
                menu_id=main_menu.id,
                menu_item_id=menu_item.id,
                display_order=i + 1,
                price_override=None  # Use base price
            )
            db.add(menu_contains)
        
        # 30% chance of having a special menu
        if random.random() < 0.3:
            special_menu = Menu(
                restaurant_id=restaurant.id,
                name="Specials",
                description=f"Special menu for {restaurant.name}",
                is_active=True
            )
            db.add(special_menu)
            db.flush()
            
            # Add 2-3 items to the special menu with price overrides
            special_items = random.sample(menu_items, min(len(menu_items), random.randint(2, 3)))
            for i, menu_item in enumerate(special_items):
                # Apply a discount for specials
                discount_price = (menu_item.base_price * Decimal("0.85")).quantize(Decimal("0.01"))
                
                menu_contains = MenuContainsMenuItem(
                    menu_id=special_menu.id,
                    menu_item_id=menu_item.id,
                    display_order=i + 1,
                    price_override=discount_price
                )
                db.add(menu_contains)
    
    db.commit()


def create_inventory_item_units(db: Session, inventory_items: Dict[str, List[Dict[str, Any]]]) -> None:
    """Create item-specific unit conversions"""
    logger.info("Creating inventory item unit conversions...")
    
    # Get all units
    units = {unit.name: unit for unit in db.query(Unit).all()}
    
    for account_id, items in inventory_items.items():
        for item_dict in items:
            item = item_dict["item"]
            category = item_dict["category"]
            
            # Create unit conversions for specific items based on category
            if category == "Produce":
                if "Kilogram" in units and "Gram" in units:
                    # For produce, add kg to g conversion (1kg = 1000g)
                    conversion = ItemSpecificUnitConversion(
                        inventory_item_id=item.id,
                        from_unit_id=units["Kilogram"].id,
                        to_unit_id=units["Gram"].id,
                        conversion_factor=Decimal("1000.00")
                    )
                    db.add(conversion)
                    
                    # Also add pound to kg conversion (1lb = 0.453592kg)
                    if "Pound" in units:
                        conversion = ItemSpecificUnitConversion(
                            inventory_item_id=item.id,
                            from_unit_id=units["Pound"].id,
                            to_unit_id=units["Kilogram"].id,
                            conversion_factor=Decimal("0.453592")
                        )
                        db.add(conversion)
            
            elif category == "Meat" or category == "Seafood":
                if "Kilogram" in units and "Pound" in units:
                    # For meat/seafood, add kg to lb conversion (1kg = 2.20462lb)
                    conversion = ItemSpecificUnitConversion(
                        inventory_item_id=item.id,
                        from_unit_id=units["Kilogram"].id,
                        to_unit_id=units["Pound"].id,
                        conversion_factor=Decimal("2.20462")
                    )
                    db.add(conversion)
                    
                    # Also add oz to kg conversion (1oz = 0.0283495kg)
                    if "Ounce" in units:
                        conversion = ItemSpecificUnitConversion(
                            inventory_item_id=item.id,
                            from_unit_id=units["Ounce"].id,
                            to_unit_id=units["Kilogram"].id,
                            conversion_factor=Decimal("0.0283495")
                        )
                        db.add(conversion)
            
            elif category == "Beverages":
                if "Liter" in units and "Milliliter" in units:
                    # For beverages, add L to mL conversion (1L = 1000mL)
                    conversion = ItemSpecificUnitConversion(
                        inventory_item_id=item.id,
                        from_unit_id=units["Liter"].id,
                        to_unit_id=units["Milliliter"].id,
                        conversion_factor=Decimal("1000.00")
                    )
                    db.add(conversion)
                    
                if "Gallon" in units and "Liter" in units:
                    # Also add gallon to L conversion (1gal = 3.78541L)
                    conversion = ItemSpecificUnitConversion(
                        inventory_item_id=item.id,
                        from_unit_id=units["Gallon"].id,
                        to_unit_id=units["Liter"].id,
                        conversion_factor=Decimal("3.78541")
                    )
                    db.add(conversion)
            
            elif category == "Bakery":
                if "Piece" in units and "Dozen" in units:
                    # For bakery items, add dozen to piece conversion (1dz = 12pc)
                    conversion = ItemSpecificUnitConversion(
                        inventory_item_id=item.id,
                        from_unit_id=units["Dozen"].id,
                        to_unit_id=units["Piece"].id,
                        conversion_factor=Decimal("12.00")
                    )
                    db.add(conversion)
    
    db.commit()


def calculate_recipe_cost(db: Session, recipe_id: uuid.UUID) -> Decimal:
    """Calculate the cost of a recipe based on its ingredients"""
    total_cost = Decimal("0.00")
    
    # Get all recipe ingredients
    ingredients = db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe_id).all()
    
    for ingredient in ingredients:
        # Get inventory item
        item = db.query(InventoryItem).filter(InventoryItem.id == ingredient.inventory_item_id).first()
        if item and item.current_cost_per_unit:
            ingredient_cost = item.current_cost_per_unit * ingredient.quantity
            total_cost += ingredient_cost
    
    return total_cost.quantize(Decimal("0.01"))


def get_category_for_recipe(recipe_name: str) -> str:
    """Determine category based on recipe name"""
    recipe_name = recipe_name.lower()
    
    if "burger" in recipe_name or "sandwich" in recipe_name:
        return "Sandwiches"
    elif "salad" in recipe_name:
        return "Salads"
    elif "pasta" in recipe_name or "rice" in recipe_name:
        return "Mains"
    elif "fish" in recipe_name or "salmon" in recipe_name or "seafood" in recipe_name:
        return "Seafood"
    elif "cake" in recipe_name or "dessert" in recipe_name:
        return "Desserts"
    else:
        return "Specialties"


def create_staff_onboardings(db: Session, restaurants: List[Restaurant]) -> None:
    """Create staff onboarding data for each restaurant"""
    logger.info("Creating staff onboarding data...")
    
    position_titles = ["Server", "Line Cook", "Host/Hostess", "Dishwasher", "Bartender"]
    
    # Standard onboarding steps for all staff
    standard_steps = [
        ("Complete Paperwork", "Complete W-4, I-9, and other required forms", StepStatus.COMPLETED),
        ("Uniform Fitting", "Get fitted for uniform and collect required items", StepStatus.COMPLETED),
        ("POS Training", "Complete training on Point of Sale system", StepStatus.IN_PROGRESS),
        ("Safety Training", "Complete workplace safety training", StepStatus.PENDING),
        ("Food Handler Certification", "Obtain local food handler certification", StepStatus.PENDING)
    ]
    
    # Position-specific steps
    position_specific_steps = {
        "Server": [
            ("Menu Knowledge Test", "Complete training and test on menu items", StepStatus.PENDING),
            ("Wine and Beverage Training", "Complete training on wine list and beverage offerings", StepStatus.PENDING)
        ],
        "Line Cook": [
            ("Kitchen Station Training", "Complete training on assigned kitchen station", StepStatus.PENDING),
            ("Recipe Book Review", "Review and demonstrate knowledge of restaurant recipes", StepStatus.PENDING)
        ],
        "Host/Hostess": [
            ("Reservation System Training", "Complete training on the reservation system", StepStatus.PENDING),
            ("Customer Service Training", "Complete customer service and conflict resolution training", StepStatus.PENDING)
        ],
        "Dishwasher": [
            ("Equipment Training", "Complete training on dishwashing equipment", StepStatus.PENDING),
            ("Chemical Safety", "Complete training on cleaning chemicals and safety", StepStatus.PENDING)
        ],
        "Bartender": [
            ("Cocktail Recipe Training", "Learn restaurant's signature cocktails", StepStatus.PENDING),
            ("Responsible Alcohol Service", "Complete alcohol service certification", StepStatus.PENDING)
        ]
    }
    
    for restaurant in restaurants:
        # Create 2-5 onboarding records per restaurant
        num_onboardings = random.randint(2, 5)
        
        for _ in range(num_onboardings):
            position = random.choice(position_titles)
            status_weights = [0.5, 0.3, 0.2]  # weights for in_progress, completed, terminated
            status = random.choices(
                [StaffStatus.IN_PROGRESS, StaffStatus.COMPLETED, StaffStatus.TERMINATED], 
                weights=status_weights
            )[0]
            
            # Set start date (between 30 days ago and 7 days from now)
            days_offset = random.randint(-30, 7)
            start_date = date.today() + timedelta(days=days_offset)
            
            staff = StaffOnboarding(
                restaurant_id=restaurant.id,
                name=f"Test Staff {random.randint(1000, 9999)}",
                email=f"staff{random.randint(1000, 9999)}@example.com",
                position=position,
                start_date=start_date,
                status=status
            )
            db.add(staff)
            db.flush()
            
            # Add standard steps for everyone
            for i, (step_name, description, default_status) in enumerate(standard_steps):
                # Adjust status based on onboarding status
                if status == StaffStatus.COMPLETED:
                    step_status = StepStatus.COMPLETED
                    completion_date = start_date + timedelta(days=i+1)
                elif status == StaffStatus.TERMINATED:
                    # Some steps completed, some not
                    if i < 3:
                        step_status = StepStatus.COMPLETED
                        completion_date = start_date + timedelta(days=i+1)
                    else:
                        step_status = StepStatus.FAILED
                        completion_date = None
                else:  # IN_PROGRESS
                    # Progressive completion
                    if i < 2:
                        step_status = StepStatus.COMPLETED
                        completion_date = start_date + timedelta(days=i+1)
                    elif i == 2:
                        step_status = default_status
                        completion_date = None
                    else:
                        step_status = StepStatus.PENDING
                        completion_date = None
                
                step = OnboardingStep(
                    staff_onboarding_id=staff.id,
                    name=step_name,
                    description=description,
                    status=step_status,
                    completion_date=completion_date
                )
                db.add(step)
            
            # Add position-specific steps
            if position in position_specific_steps:
                for i, (step_name, description, default_status) in enumerate(position_specific_steps[position]):
                    # Adjust status based on onboarding status
                    if status == StaffStatus.COMPLETED:
                        step_status = StepStatus.COMPLETED
                        completion_date = start_date + timedelta(days=len(standard_steps)+i+1)
                    elif status == StaffStatus.TERMINATED:
                        step_status = StepStatus.FAILED
                        completion_date = None
                    else:  # IN_PROGRESS
                        step_status = StepStatus.PENDING
                        completion_date = None
                    
                    step = OnboardingStep(
                        staff_onboarding_id=staff.id,
                        name=step_name,
                        description=description,
                        status=step_status,
                        completion_date=completion_date
                    )
                    db.add(step)
    
    db.commit()


class StaffStatus:
    """Enum values for staff onboarding status"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class StepStatus:
    """Enum values for onboarding step status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"