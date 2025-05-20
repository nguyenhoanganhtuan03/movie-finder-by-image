from fastapi import APIRouter, UploadFile, File, FastAPI
from app.controllers.finder_controller import predict_film

app = FastAPI()
router = APIRouter(prefix="/finder", tags=["Film Finder"])

@router.post("/predict")
async def find_film(file: UploadFile = File(...)):
    return await predict_film(file)

# Thêm route vào FastAPI app
app.include_router(router)