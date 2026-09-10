import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
import redis.asyncio as aioredis
from backend.app.core.config import settings
from backend.app.core.logging import logger

class InMemoryStreamEngine:
    """In-memory Redis Streams emulator supporting consumer groups, ACKs, and claims."""
    def __init__(self):
        self._streams: Dict[str, List[Tuple[str, Dict[str, str]]]] = {}
        self._groups: Dict[str, Dict[str, Dict[str, Any]]] = {} # stream -> group_name -> {last_id, consumers, pel}
        self._lock = asyncio.Lock()
        self._seq = 0

    async def xadd(self, stream: str, fields: Dict[str, str]) -> str:
        async with self._lock:
            if stream not in self._streams:
                self._streams[stream] = []
            self._seq += 1
            entry_id = f"{int(time.time() * 1000)}-{self._seq}"
            self._streams[stream].append((entry_id, fields))
            return entry_id

    async def xgroup_create(self, stream: str, groupname: str, id: str = "$", mkstream: bool = True):
        async with self._lock:
            if stream not in self._streams and mkstream:
                self._streams[stream] = []
            if stream not in self._groups:
                self._groups[stream] = {}
            if groupname not in self._groups[stream]:
                last_id = "0-0" if id == "0" else (self._streams[stream][-1][0] if self._streams[stream] else "0-0")
                self._groups[stream][groupname] = {
                    "last_id": last_id,
                    "consumers": {},
                    "pel": {} # entry_id -> {consumer, delivery_time, delivery_count, data}
                }

    async def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        streams: Dict[str, str],
        count: Optional[int] = None,
        block: Optional[int] = None
    ) -> List[Tuple[str, List[Tuple[str, Dict[str, str]]]]]:
        async with self._lock:
            result = []
            for stream, stream_id in streams.items():
                if stream not in self._streams or stream not in self._groups or groupname not in self._groups[stream]:
                    continue
                grp = self._groups[stream][groupname]
                grp["consumers"][consumername] = time.time()
                
                entries_to_return = []
                
                # If stream_id is ">", read new unread messages
                if stream_id == ">":
                    for entry_id, fields in self._streams[stream]:
                        if entry_id > grp["last_id"]:
                            entries_to_return.append((entry_id, fields))
                            grp["pel"][entry_id] = {
                                "consumer": consumername,
                                "delivery_time": time.time(),
                                "delivery_count": 1,
                                "fields": fields
                            }
                            grp["last_id"] = entry_id
                            if count and len(entries_to_return) >= count:
                                break
                elif stream_id == "0":
                    # Read pending messages for this consumer
                    for entry_id, pel_info in list(grp["pel"].items()):
                        if pel_info["consumer"] == consumername:
                            entries_to_return.append((entry_id, pel_info["fields"]))
                            if count and len(entries_to_return) >= count:
                                break

                if entries_to_return:
                    result.append((stream, entries_to_return))

            return result

    async def xack(self, stream: str, groupname: str, *ids: str) -> int:
        async with self._lock:
            if stream not in self._groups or groupname not in self._groups[stream]:
                return 0
            grp = self._groups[stream][groupname]
            acked = 0
            for entry_id in ids:
                if entry_id in grp["pel"]:
                    del grp["pel"][entry_id]
                    acked += 1
            return acked

    async def xlen(self, stream: str) -> int:
        async with self._lock:
            return len(self._streams.get(stream, []))

    async def xpending(self, stream: str, groupname: str) -> Dict[str, Any]:
        async with self._lock:
            if stream not in self._groups or groupname not in self._groups[stream]:
                return {"pending": 0, "min": None, "max": None, "consumers": []}
            grp = self._groups[stream][groupname]
            pel = grp["pel"]
            return {"pending": len(pel), "min": min(pel.keys()) if pel else None, "max": max(pel.keys()) if pel else None}

    async def xautoclaim(
        self,
        stream: str,
        groupname: str,
        consumername: str,
        min_idle_time: int,
        start_id: str = "0-0",
        count: int = 10
    ) -> Tuple[str, List[Tuple[str, Dict[str, str]]], List[str]]:
        async with self._lock:
            if stream not in self._groups or groupname not in self._groups[stream]:
                return ("0-0", [], [])
            grp = self._groups[stream][groupname]
            now = time.time()
            min_idle_sec = min_idle_time / 1000.0
            claimed = []
            
            for entry_id, pel_info in list(grp["pel"].items()):
                if entry_id >= start_id:
                    if (now - pel_info["delivery_time"]) >= min_idle_sec:
                        pel_info["consumer"] = consumername
                        pel_info["delivery_time"] = now
                        pel_info["delivery_count"] += 1
                        claimed.append((entry_id, pel_info["fields"]))
                        if len(claimed) >= count:
                            break
            return ("0-0", claimed, [])

_in_memory_stream_engine = InMemoryStreamEngine()
_redis_client: Optional[aioredis.Redis] = None
_redis_client_loop: Optional[asyncio.AbstractEventLoop] = None
_is_using_embedded = False

async def get_redis_client() -> Tuple[Any, bool]:
    """
    Returns (client, is_embedded) supporting both real Redis and the fallback engine.
    Ensures Redis client connection pool is cleanly bound to the current running event loop.
    """
    global _redis_client, _redis_client_loop, _is_using_embedded
    
    current_loop = asyncio.get_running_loop()
    
    # If a client exists, verify it belongs to the active running event loop
    if _redis_client is not None:
        if _redis_client_loop is current_loop and not current_loop.is_closed():
            return _redis_client, False
        else:
            # Client was created on a previous or closed loop; close and reset
            try:
                if _redis_client_loop and not _redis_client_loop.is_closed():
                    await _redis_client.aclose()
            except Exception:
                pass
            _redis_client = None
            _redis_client_loop = None

    if _is_using_embedded:
        return _in_memory_stream_engine, True

    try:
        client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0
        )
        await client.ping()
        _redis_client = client
        _redis_client_loop = current_loop
        _is_using_embedded = False
        logger.info("Connected to external Redis server", extra={"redis_url": settings.REDIS_URL})
        return _redis_client, False
    except Exception as e:
        if not settings.USE_EMBEDDED_STREAM_FALLBACK:
            logger.error(f"External Redis unavailable at {settings.REDIS_URL} and fallback is disabled: {e}")
            raise ConnectionError(f"External Redis unavailable at {settings.REDIS_URL}") from e
            
        logger.warning(
            f"External Redis unavailable ({e}). Initializing embedded Redis Streams engine for high-performance zero-dependency execution."
        )
        _is_using_embedded = True
        return _in_memory_stream_engine, True

async def close_redis():
    """Cleanly closes active Redis client connection pool."""
    global _redis_client, _redis_client_loop
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception as e:
            logger.warning(f"Error closing Redis client: {e}")
        finally:
            _redis_client = None
            _redis_client_loop = None

def reset_redis_state():
    """Resets client reference, embedded flag, and in-memory streams (used in test fixtures)."""
    global _redis_client, _redis_client_loop, _is_using_embedded, _in_memory_stream_engine
    _redis_client = None
    _redis_client_loop = None
    _is_using_embedded = False
    _in_memory_stream_engine = InMemoryStreamEngine()


