"""Entrypoint for the background ingestion worker container: `python -m api.pipeline.worker`."""

import logging

from rq import Worker

from api.services.queue import ingestion_queue, redis_conn

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    worker = Worker([ingestion_queue], connection=redis_conn)
    worker.work()
