import redis.asyncio as redis
import os
import json
from typing import List, Dict, Optional

class ConversationState:
    """
    Manages conversation state for active calls using Redis.
    Provides low-latency access to history and collected patient data.
    """
    
    def __init__(self):
        # Redis connection URL from environment or fallback
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = 3600  # 1 hour session expiry
        
    async def create_session(self, call_sid: str, business_id: str, caller_phone: str):
        """Initialize a new session in Redis"""
        key = f"call_session:{call_sid}"
        session_data = {
            "business_id": business_id,
            "caller_phone": caller_phone,
            "created_at": str(os.getenv("CURRENT_TIME", "now")),
            "history": json.dumps([]),
            "collected_data": json.dumps({})
        }
        await self.redis.hset(key, mapping=session_data)
        await self.redis.expire(key, self.ttl)
        
    async def add_turn(self, call_sid: str, role: str, content: str):
        """Append a turn to the conversation history"""
        key = f"call_session:{call_sid}"
        history_raw = await self.redis.hget(key, "history")
        history = json.loads(history_raw) if history_raw else []
        history.append({"role": role, "content": content})
        await self.redis.hset(key, "history", json.dumps(history))
        await self.redis.expire(key, self.ttl)
            
    async def get_history(self, call_sid: str) -> List[Dict]:
        """Retrieve full conversation history"""
        key = f"call_session:{call_sid}"
        history_raw = await self.redis.hget(key, "history")
        return json.loads(history_raw) if history_raw else []

    async def update_collected_data(self, call_sid: str, data: Dict):
        """Store structured data collected by the AI (e.g. appointment preference)"""
        key = f"call_session:{call_sid}"
        existing_raw = await self.redis.hget(key, "collected_data")
        existing = json.loads(existing_raw) if existing_raw else {}
        existing.update(data)
        await self.redis.hset(key, "collected_data", json.dumps(existing))

    async def get_session_info(self, call_sid: str) -> Optional[Dict]:
        """Get all session metadata"""
        key = f"call_session:{call_sid}"
        return await self.redis.hgetall(key)

    async def end_session(self, call_sid: str):
        """Cleanup session data after call ends"""
        key = f"call_session:{call_sid}"
        await self.redis.delete(key)

    async def close(self):
        """Close Redis connection"""
        await self.redis.close()
