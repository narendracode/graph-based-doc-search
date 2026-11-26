import redis
from rq import Queue

from api.config import get_settings

settings = get_settings()

redis_conn = redis.from_url(settings.redis_url)
# RQ's own default job timeout (180s) is too short for this pipeline: the
# graph_building step does CPU-only inference against an 8B-parameter chat
# model (no GPU on the deployment boxes), which alone can take longer than
# that for a single entity-extraction call, on top of parsing + per-chunk
# embedding calls counted against the same budget.
ingestion_queue = Queue(settings.queue_name, connection=redis_conn, default_timeout=900)
