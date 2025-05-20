from fastapi import UploadFile
import shutil
import os
from app.models.run_model_faiss import predict_film_auto

# Đường dẫn thư mục tạm để lưu file ảnh hoặc video
TEMP_UPLOAD_DIR = "backend/app/uploads/upload_temps"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# Hàm để dự đoán phim từ file ảnh hoặc video
async def predict_film(file: UploadFile):
    try:
        # Tạo đường dẫn lưu file tạm
        file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)

        # Ghi nội dung file ra đĩa
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Gọi hàm dự đoán từ run_model
        prediction = predict_film_auto(file_path)

        # Xóa file sau khi xử lý (tuỳ bạn nếu muốn giữ lại để debug)
        os.remove(file_path)

        return {"filename": file.filename, "predicted_film": prediction}

    except Exception as e:
        return {"error": str(e)}
