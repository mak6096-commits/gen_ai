import os
from sqlmodel import SQLModel, create_engine, Session
from app.models import Product, Order

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./orders_inventory.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)


def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session


# In-memory storage as fallback (for demo purposes)
class InMemoryStore:
    def __init__(self):
        self.products = {}
        self.orders = {}
        self.product_counter = 1
        self.order_counter = 1
        
    def reset(self):
        """Reset all data - useful for testing"""
        self.products.clear()
        self.orders.clear()
        self.product_counter = 1
        self.order_counter = 1


# Global in-memory store instance
memory_store = InMemoryStore()
