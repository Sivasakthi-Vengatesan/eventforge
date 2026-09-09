import json
from typing import Any, Dict, List, Optional, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.queue.redis_client import get_redis_client

class StreamManager:
    def __init__(self, stream_name: str = settings.STREAM_NAME, group_name: str = settings.CONSUMER_GROUP):
        self.stream_name = stream_name
        self.group_name = group_name

    async def init_stream(self):
        client, is_embedded = await get_redis_client()
        try:
            if is_embedded:
                await client.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
            else:
                try:
                    await client.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
                except Exception as e:
                    if "BUSYGROUP" not in str(e):
                        logger.warning(f"Error initializing consumer group: {e}")
        except Exception as err:
            logger.error(f"Failed to initialize stream and group: {err}")

    async def push_event(
        self,
        event_id: str,
        provider: str,
        event_type: str,
        payload: Dict[str, Any],
        retry_count: int = 0
    ) -> str:
        client, _ = await get_redis_client()
        entry_data = {
            "event_id": event_id,
            "provider": provider,
            "event_type": event_type,
            "payload": json.dumps(payload),
            "retry_count": str(retry_count)
        }
        entry_id = await client.xadd(self.stream_name, entry_data)
        return entry_id

    async def read_events(
        self,
        consumer_name: str,
        count: int = 5,
        block_ms: int = 500
    ) -> List[Tuple[str, Dict[str, Any]]]:
        client, _ = await get_redis_client()
        try:
            response = await client.xreadgroup(
                self.group_name,
                consumer_name,
                {self.stream_name: ">"},
                count=count,
                block=block_ms
            )
            
            parsed = []
            if response:
                for stream, messages in response:
                    for msg_id, data in messages:
                        try:
                            payload_obj = json.loads(data.get("payload", "{}"))
                        except Exception:
                            payload_obj = data.get("payload")
                            
                        parsed.append((msg_id, {
                            "event_id": data.get("event_id"),
                            "provider": data.get("provider"),
                            "event_type": data.get("event_type"),
                            "payload": payload_obj,
                            "retry_count": int(data.get("retry_count", 0))
                        }))
            return parsed
        except Exception as e:
            logger.error(f"Error reading from Redis Stream {self.stream_name}: {e}")
            return []

    async def ack_event(self, msg_id: str) -> int:
        client, _ = await get_redis_client()
        try:
            return await client.xack(self.stream_name, self.group_name, msg_id)
        except Exception as e:
            logger.error(f"Error ACKing message {msg_id}: {e}")
            return 0

    async def claim_stuck_events(
        self,
        consumer_name: str,
        min_idle_ms: int = 15000,
        count: int = 5
    ) -> List[Tuple[str, Dict[str, Any]]]:
        client, is_embedded = await get_redis_client()
        try:
            res = await client.xautoclaim(
                self.stream_name,
                self.group_name,
                consumer_name,
                min_idle_time=min_idle_ms,
                start_id="0-0",
                count=count
            )
            # xautoclaim returns (next_start_id, messages, deleted_ids)
            messages = res[1] if isinstance(res, (list, tuple)) and len(res) > 1 else []
            parsed = []
            for msg_id, data in messages:
                try:
                    payload_obj = json.loads(data.get("payload", "{}"))
                except Exception:
                    payload_obj = data.get("payload")
                    
                parsed.append((msg_id, {
                    "event_id": data.get("event_id"),
                    "provider": data.get("provider"),
                    "event_type": data.get("event_type"),
                    "payload": payload_obj,
                    "retry_count": int(data.get("retry_count", 0))
                }))
            return parsed
        except Exception as e:
            logger.error(f"Error claiming stuck events: {e}")
            return []

    async def get_queue_stats(self) -> Dict[str, int]:
        client, _ = await get_redis_client()
        try:
            total_len = await client.xlen(self.stream_name)
            pending_res = await client.xpending(self.stream_name, self.group_name)
            pending_count = pending_res.get("pending", 0) if isinstance(pending_res, dict) else (pending_res[0] if isinstance(pending_res, (list, tuple)) else 0)
            return {
                "stream_length": total_len,
                "pending_count": pending_count,
                "queue_depth": total_len
            }
        except Exception:
            return {"stream_length": 0, "pending_count": 0, "queue_depth": 0}

stream_manager = StreamManager()
