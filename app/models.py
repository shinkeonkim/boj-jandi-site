from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    handle: str = Field(index=True, unique=True)
    last_scraped_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="none") # none, pending, completed, error
    
    solved_problems: List["SolvedProblem"] = Relationship(back_populates="user")

class SolvedProblem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    problem_id: int = Field(index=True)
    
    user: User = Relationship(back_populates="solved_problems")
