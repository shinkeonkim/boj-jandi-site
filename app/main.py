from fastapi import FastAPI, Request, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import os
from datetime import datetime, timedelta

from app.database import create_db_and_tables, get_session
from app.scraper import run_background_scrape
from app.models import User

app = FastAPI(title="BOJ Jandi")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/search")
async def search(handle: str = Form(...)):
    return RedirectResponse(url=f"/user/{handle}", status_code=303)

@app.get("/user/{handle}", response_class=HTMLResponse)
async def user_grass(request: Request, handle: str):
    return templates.TemplateResponse("grass.html", {"request": request, "handle": handle})

@app.get("/api/grass/{handle}")
async def get_grass_api(handle: str, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.handle == handle)).first()
    now = datetime.utcnow()

    # Case 1: New User
    if not user:
        user = User(handle=handle, status="pending", last_scraped_at=now)
        session.add(user)
        session.commit()
        session.refresh(user)
        background_tasks.add_task(run_background_scrape, handle)
        return {"status": "pending", "pids": []}

    # Case 2: Existing User, check cache
    is_recent = (now - user.last_scraped_at < timedelta(hours=1))
    
    if user.status == "completed" and is_recent:
        pids = [sp.problem_id for sp in user.solved_problems]
        return {"status": "completed", "pids": pids, "refreshed": False}

    # Case 3: Need Refresh (Old data or Error or stuck Pending for too long?)
    # If it's already pending and recent (< 1 min?), just wait
    if user.status == "pending":
         # Simple timeout check: if pending for > 2 minutes, restart
         if now - user.last_scraped_at > timedelta(minutes=2):
             user.last_scraped_at = now # Reset timer
             session.add(user)
             session.commit()
             background_tasks.add_task(run_background_scrape, handle)
         return {"status": "pending", "pids": []}

    # Case 4: Status completed but old, or error -> Trigger Refresh
    user.status = "pending"
    user.last_scraped_at = now
    session.add(user)
    session.commit()
    background_tasks.add_task(run_background_scrape, handle)
    
    # Return old data while refreshing if available
    pids = [sp.problem_id for sp in user.solved_problems]
    return {"status": "pending", "pids": pids}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
