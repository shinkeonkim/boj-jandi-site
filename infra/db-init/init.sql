-- Database initialization script
-- SQLModel will handle table creation, but this is a placeholder for any custom migrations or initial data.
CREATE TABLE IF NOT EXISTS initial_check (
    id SERIAL PRIMARY KEY,
    initialized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
