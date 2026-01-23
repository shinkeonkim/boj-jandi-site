from fastapi import FastAPI, Request, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import os
from datetime import datetime, timedelta

from app.database import create_db_and_tables, get_session
from app.scraper import run_background_scrape
from app.models import User, ProblemTier
from fastapi import FastAPI, Request, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import os
from datetime import datetime, timedelta

from app.database import create_db_and_tables, get_session
from app.scraper import run_background_scrape

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

from typing import List
from pydantic import BaseModel

class PidsRequest(BaseModel):
    pids: List[int]

@app.post("/api/grass/details")
async def get_grass_details(body: PidsRequest, session: Session = Depends(get_session)):
    if not body.pids:
        return {}
        
    statement = select(ProblemTier).where(ProblemTier.problem_id.in_(body.pids))
    results = session.exec(statement).all()
    
    details = {}
    for pt in results:
        details[pt.problem_id] = {
            "tier": pt.tier,
            "title": pt.title
        }
    return details

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
    
    if user.status in ["completed", "not_found", "error"] and is_recent:
        pids = [sp.problem_id for sp in user.solved_problems] if user.status == "completed" else []
        return {"status": user.status, "pids": pids, "refreshed": False}

    # Case 3: Need Refresh
    if user.status == "pending":
         if now - user.last_scraped_at > timedelta(minutes=2):
             user.last_scraped_at = now
             session.add(user)
             session.commit()
             background_tasks.add_task(run_background_scrape, handle)
         return {"status": "pending", "pids": []}

    # Case 4: Refresh needed
    user.status = "pending"
    user.last_scraped_at = now
    session.add(user)
    session.commit()
    background_tasks.add_task(run_background_scrape, handle)
    
    # Return old data while refreshing
    pids = [sp.problem_id for sp in user.solved_problems]
    return {"status": "pending", "pids": pids}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
