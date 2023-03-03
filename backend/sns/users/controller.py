from fastapi import APIRouter

router = APIRouter(prefix='/users')

@router.get("/")
def root():
    return {"message": "Hello world"}