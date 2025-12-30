from jose import jwt
import datetime
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from api.common.config import settings

def generate_dev_token(role="CHILD"):
    payload = {
        "sub": "dev-user",
        "role": role,
        "device_id": "dev-device",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    print(f"Using secret: {settings.JWT_SECRET}")
    print(token)

if __name__ == "__main__":
    role = sys.argv[1] if len(sys.argv) > 1 else "CHILD"
    generate_dev_token(role)
