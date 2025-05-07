from fastapi import FastAPI
from .database import engine, Base
from .routes import auth, task

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()

app.include_router(auth.router)
app.include_router(task.router)

@app.on_event("startup")
async def startup():
    await create_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)