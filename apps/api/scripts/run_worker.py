import asyncio
import sys
from pathlib import Path

# Add src/ to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger
from modules.intelligence.application.worker import worker as intelligence_worker
from modules.inventory.application.cron_worker import worker as cron_worker

async def main():
    logger.info("Starting Michi Standalone Background Workers (Forecasting & Cron)...")
    
    # Run both background loops concurrently in this process
    await asyncio.gather(
        intelligence_worker.start(),
        cron_worker.start()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Workers stopped by user.")
