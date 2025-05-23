import re
from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo
from pydantic_core import PydanticCustomError

class PasswordMixin:
    """Mixin class for password validation."""

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str, info: ValidationInfo) -> str:
        """
        The Password Should be:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        errors = []
        
        if not re.search(r"[A-Z]", value):
            errors.append("at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            errors.append("at least one lowercase letter")
        if not re.search(r"\d", value):
            errors.append("at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            errors.append("at least one special character")
        
        if errors:
            raise PydanticCustomError(
                'password_validation',
                'Password must contain {errors}',
                {'errors': ', '.join(errors)}
            )
        
        return value
