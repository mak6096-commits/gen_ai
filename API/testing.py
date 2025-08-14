from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

user_db = {
    1: {"name": "John", "age": 30},
    2: {"name": "Jane", "age": 25},
    3: {"name": "Alice", "age": 28}
}

class User(BaseModel):
    name: str
    age: int

# GET endpoint to retrieve all users
@app.get("/user_db/data/v1/users")
def get_all_users():
    return {"users": user_db}

# GET endpoint to retrieve a specific user
@app.get("/user_db/data/v1/user/{user_id}")
def get_user(user_id: int):
    if user_id in user_db:
        return {"user": user_db[user_id]}
    else:
        return {"message": "User not found"}, 404

# POST endpoint to create a new user
@app.post("/user_db/data/v1/create")
def create_user(user: User):
    # Generate new user ID
    new_id = max(user_db.keys()) + 1 if user_db else 1
    user_db[new_id] = user.dict()
    return {"message": "User created successfully", "user_id": new_id, "user": user_db[new_id]}

@app.put("/user_db/data/v1/update/{user_id}")
def update_user(user_id: int, user: User):
    if user_id in user_db:
        user_db[user_id] = user.dict()
        return {"message": "User updated successfully", "user": user_db[user_id]}
    else:
        return {"message": "User not found"}, 404

print("user_db:", user_db)

@app.delete("/user_db/data/v1/delete/{user_id}")
def delete_user(user_id: int):
    if user_id in user_db:
        del user_db[user_id]
        return {"message": "User deleted successfully"}
    else:
        return {"message": "User not found"}, 404

print("user_db:", user_db)

