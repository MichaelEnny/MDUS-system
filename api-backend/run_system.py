"""
MDUS System Runner
Starts all components of the file storage and processing pipeline
"""

import asyncio
import uvicorn
import logging
from multiprocessing import Process
import signal
import sys

from app.services.processing_worker import start_worker, stop_worker
from app.services.lifecycle_manager import start_lifecycle_manager, stop_lifecycle_manager

logger = logging.getLogger(__name__)

class MDUSSystemRunner:
    """Coordinates all system components"""
    
    def __init__(self):
        self.api_process = None
        self.worker_task = None
        self.lifecycle_task = None
        self.is_running = False
    
    async def start_background_services(self):
        """Start background services"""
        
        logger.info("Starting background services...")
        
        # Start processing worker
        self.worker_task = asyncio.create_task(start_worker())
        
        # Start lifecycle manager  
        self.lifecycle_task = asyncio.create_task(start_lifecycle_manager())
        
        logger.info("Background services started")
    
    async def stop_background_services(self):
        """Stop background services"""
        
        logger.info("Stopping background services...")
        
        # Stop processing worker
        if self.worker_task:
            await stop_worker()
            self.worker_task.cancel()
        
        # Stop lifecycle manager
        if self.lifecycle_task:
            stop_lifecycle_manager()
            self.lifecycle_task.cancel()
        
        logger.info("Background services stopped")
    
    def start_api_server(self):
        """Start FastAPI server"""
        
        logger.info("Starting API server...")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0", 
            port=8000,
            reload=False,  # Disable reload in production
            log_level="info",
            access_log=True
        )
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        
        logger.info(f"Received signal {signum}, shutting down...")
        self.is_running = False
        
        # Stop background services
        if self.worker_task or self.lifecycle_task:
            asyncio.create_task(self.stop_background_services())
        
        sys.exit(0)
    
    async def run_integrated(self):
        """Run all services in integrated mode"""
        
        logger.info("Starting MDUS System (Integrated Mode)")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.is_running = True
        
        try:
            # Start background services
            await self.start_background_services()
            
            # Start API server (blocks until shutdown)
            server_config = uvicorn.Config(
                "main:app",
                host="0.0.0.0",
                port=8000, 
                log_level="info",
                reload=False
            )
            server = uvicorn.Server(server_config)
            
            # Run until stopped
            await server.serve()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"System error: {e}")
        finally:
            # Clean shutdown
            await self.stop_background_services()
            logger.info("MDUS System shutdown complete")

def run_api_only():
    """Run API server only (for development)"""
    
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting MDUS API Backend (API Only Mode)")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable reload for development
        log_level="info"
    )

def run_worker_only():
    """Run processing worker only"""
    
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting MDUS Processing Worker (Worker Only Mode)")
    
    asyncio.run(start_worker())

def run_lifecycle_only():
    """Run lifecycle manager only"""
    
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting MDUS Lifecycle Manager (Lifecycle Only Mode)")
    
    asyncio.run(start_lifecycle_manager())

async def run_full_system():
    """Run complete system with all components"""
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    runner = MDUSSystemRunner()
    await runner.run_integrated()

if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    
    if mode == "api":
        run_api_only()
    elif mode == "worker": 
        run_worker_only()
    elif mode == "lifecycle":
        run_lifecycle_only()
    elif mode == "full":
        asyncio.run(run_full_system())
    else:
        print("Usage: python run_system.py [api|worker|lifecycle|full]")
        print("  api       - Run API server only (development mode)")
        print("  worker    - Run processing worker only")  
        print("  lifecycle - Run lifecycle manager only")
        print("  full      - Run complete system (default)")
        sys.exit(1)