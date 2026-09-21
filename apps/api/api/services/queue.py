import redis
from rq import Queue

from api.config import get_settings

settings = get_settings()

redis_conn = redis.from_url(settings.redis_url)
ingestion_queue = Queue("ingestion", connection=redis_conn)
