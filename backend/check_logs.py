import asyncio
import os
import sys
from sqlalchemy import select
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.getcwd())

async def check():
    from app.database import AsyncSessionLocal, AuditLogDB
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AuditLogDB).order_by(AuditLogDB.created_at.desc()).limit(10))
        logs = result.scalars().all()
        if not logs:
            print("No logs found.")
        for l in logs:
            print(f"[{l.created_at}] {l.action}: {l.details}")

if __name__ == "__main__":
    asyncio.run(check())
