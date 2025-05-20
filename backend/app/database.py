import motor.motor_asyncio
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

# Hàm kiểm tra kết nối
async def check_connection():
    try:
        await client.admin.command("ping")
        print("✅ Kết nối MongoDB thành công!")
    except Exception as e:
        print("❌ Kết nối MongoDB thất bại:", e)

# # Nếu chạy trực tiếp file này thì thực hiện kiểm tra kết nối
# if __name__ == "__main__":
#     asyncio.run(check_connection())
