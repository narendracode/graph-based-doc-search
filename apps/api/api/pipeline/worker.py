"""Entrypoint for the background ingestion worker container: `python -m api.pipeline.worker`."""

import logging

from rq import Worker

from api.pipeline.ingest import reconcile_orphaned_documents
from api.services.queue import ingestion_queue, redis_conn

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    reconcile_orphaned_documents()
    worker = Worker([ingestion_queue], connection=redis_conn)
    worker.work()
