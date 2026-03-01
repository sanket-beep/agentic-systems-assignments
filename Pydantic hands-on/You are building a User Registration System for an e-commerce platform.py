from pydantic import BaseModel, Field, EmailStr, ValidationError

class Address(BaseModel):
    city: str = Field(..., min_length=3)
    pincode: str = Field(..., pattern=r"^\d{6}$")

class User(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    age: int = Field(..., ge=18)
    address: Address
    is_premium: bool = Field(default=False)

try:
    user_data = {
        "user_id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 25,
        "address": {
            "city": "Mumbai",
            "pincode": "400001"
        },
        "is_premium": True
    }
    user = User(**user_data)
    print("Validation Successful:", user.model_dump())
except ValidationError as e:
    print("Validation Error:", e.json())
