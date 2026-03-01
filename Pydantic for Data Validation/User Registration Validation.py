from pydantic import BaseModel, ValidationError, EmailStr, field_validator

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    age: int

    @field_validator('username')
    def validate_username_length(cls, v: str) -> str:
        if len(v) < 5:
            raise ValueError('Username must be at least 5 characters long')
        return v

    @field_validator('age')
    def validate_age_limit(cls, v: int) -> int:
        if v < 18:
            raise ValueError('You must be at least 18 years old to register')
        return v

valid_data = {
    "username": "johndoe",
    "email": "john.doe@example.com",
    "age": 25
}

invalid_data = {
    "username": "jd",
    "email": "not-an-email",
    "age": 16
}

try:
    user_valid = UserRegister(**valid_data)
    print(f"Valid user registered: {user_valid.model_dump_json(indent=2)}")
except ValidationError as e:
    print("Validation Error for valid data:")
    print(e.json(indent=2))

try:
    user_invalid = UserRegister(**invalid_data)
    print(f"Invalid user registered: {user_invalid.model_dump_json(indent=2)}")
except ValidationError as e:
    print("Validation Error for invalid data:")
    # Pretty print the errors
    print(e.json(indent=2))