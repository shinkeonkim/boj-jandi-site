from bs4 import BeautifulSoup
from datetime import datetime
from sqlmodel import Session, select, create_engine
from app.models import User, SolvedProblem
import os
import time
import random
from playwright.sync_api import sync_playwright

# Create a new engine for background tasks
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "bojjandi")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{POSTGRES_DB}"

bg_engine = create_engine(DATABASE_URL)

BASE_URL = "https://www.acmicpc.net"

def scrape_solved_problems(handle: str):
    url = f"{BASE_URL}/user/{handle}"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print(f"Navigating to {url} with Playwright...")
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if response.status == 404:
                print(f"User {handle} not found (404)")
                browser.close()
                return None
            
            # Additional wait to ensure dynamic content or WAF check completes
            # WAF might show a challenge, Playwright usually handles JS-based challenges automatically if we wait
            page.wait_for_timeout(3000) 
            
            content = page.content()
            browser.close()
            
            soup = BeautifulSoup(content, "html.parser")
            
            solved_div = None
            panels = soup.select(".panel")
            for panel in panels:
                title = panel.select_one(".panel-title")
                if title and "맞은 문제" in title.get_text():
                    solved_div = panel.select_one(".problem-list")
                    print("Found solved_div with panel title '맞은 문제'")
                    break
                    
            if not solved_div:
                solved_div = soup.select_one(".problem-list")

            if not solved_div:
                print(f"No solved_div found for {handle}.")
                # Debug: check if we are on a challenge page
                if "challenge" in content.lower() or "waf" in content.lower():
                     print("Seems like we are still stuck at WAF challenge.")
                return []

            problem_links = solved_div.select("a[href^='/problem/']")
            pids = []
            for link in problem_links:
                try:
                    pid_text = link.get_text().strip()
                    if pid_text.isdigit():
                        pids.append(int(pid_text))
                except:
                    continue
            
            print(f"Total valid PIDs for {handle}: {len(pids)}")
            return pids

    except Exception as e:
        print(f"Error scraping {handle} with Playwright: {e}")
        return None

def run_background_scrape(handle: str):
    """Background task to scrape and save data."""
    print(f"Starting background scrape for {handle}")
    with Session(bg_engine) as session:
        user = session.exec(select(User).where(User.handle == handle)).first()
        if not user:
            print(f"User {handle} not found in DB during background task")
            return

        try:
            pids = scrape_solved_problems(handle)
            if pids is None:
                user.status = "error"
                session.add(user)
                session.commit()
                print(f"Scrape failed (None returned) for {handle}")
                return

            # Update DB
            now = datetime.utcnow()
            user.last_scraped_at = now
            user.status = "completed"
            
            # Reset existing
            existing_pids = {sp.problem_id for sp in user.solved_problems}
            new_pids = set(pids) - existing_pids
            
            for pid in new_pids:
                sp = SolvedProblem(user_id=user.id, problem_id=pid)
                session.add(sp)
            
            session.add(user)
            session.commit()
            print(f"Background scrape completed for {handle}. Added {len(new_pids)} new problems.")
            
        except Exception as e:
            print(f"Exception in background scraping: {e}")
            user.status = "error"
            session.add(user)
            session.commit()
