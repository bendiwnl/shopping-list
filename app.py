from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Database setup
DATABASE_URL = "sqlite:///./shopping_list.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Shopping List Item model
class ShoppingListItemDB(Base):
    __tablename__ = "shopping_list"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    quantity = Column(Integer)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Pydantic model for request/response
class ShoppingListItem(BaseModel):
    id: int
    name: str
    quantity: int

    class Config:
        from_attributes = True

# FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Add an item to the shopping list
@app.post("/items/", response_model=ShoppingListItem)
def add_item(item: ShoppingListItem, db: Session = Depends(get_db)):
    db_item = ShoppingListItemDB(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Get all items in the shopping list
@app.get("/items/", response_model=list[ShoppingListItem])
def get_items(db: Session = Depends(get_db)):
    return db.query(ShoppingListItemDB).all()

# Delete an item from the shopping list
@app.delete("/items/{item_id}", response_model=ShoppingListItem)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ShoppingListItemDB).filter(ShoppingListItemDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return item