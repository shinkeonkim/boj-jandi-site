import httpx
import time
from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import ProblemTier

# Solved.ac API
API_URL = "https://solved.ac/api/v3/problem/lookup"

def fetch_tiers(start_id, end_id):
    """
    Fetches tier info for problems in range [start_id, end_id).
    Fetching is done in batches of 100.
    """
    with Session(engine) as session:
        for i in range(start_id, end_id, 100):
            pids = list(range(i, min(i + 100, end_id)))
            ids_str = ",".join(map(str, pids))
            
            try:
                print(f"Fetching batch {i} ~ {i+99}...", end=" ")
                response = httpx.get(f"{API_URL}?problemIds={ids_str}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Got {len(data)} items.")
                    
                    for item in data:
                        pid = item['problemId']
                        tier = item['level']
                        title = item['titleKo']
                        
                        existing = session.get(ProblemTier, pid)
                        if existing:
                            existing.tier = tier
                            existing.title = title
                            session.add(existing)
                        else:
                            new_pt = ProblemTier(problem_id=pid, tier=tier, title=title)
                            session.add(new_pt)
                    
                    session.commit()
                else:
                    print(f"Error: {response.status_code}")
                
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"Exception: {e}")
                time.sleep(1)

import sys

def main():
    print("Initializing Database...")
    create_db_and_tables()
    
    start = 1000
    end = 32000
    
    if len(sys.argv) >= 3:
        start = int(sys.argv[1])
        end = int(sys.argv[2])
    
    print(f"Starting Tier Collection for range {start} ~ {end}...")
    try:
        fetch_tiers(start, end)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    print("Done collection.")


if __name__ == "__main__":
    main()
