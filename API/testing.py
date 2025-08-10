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

