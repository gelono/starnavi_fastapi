from fastapi import FastAPI
from app.routers.posts import router as posts
from app.routers.users import router as users
from app.routers.comments import router as comments
from app.routers.analytics import router as analytics

app = FastAPI()
app.include_router(router=posts)
app.include_router(router=users)
app.include_router(router=comments)
app.include_router(router=analytics)


@app.get("/")
async def echo(message: str = "FAST API App 'Posts and Comments'"):
    return {"message": message}
