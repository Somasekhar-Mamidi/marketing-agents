"""Parallel processing utilities for event pipeline."""

import logging
import time
from typing import List, Dict, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a single item."""
    item_id: str
    success: bool
    result: Any
    duration_ms: float
    error: Optional[str] = None


class ParallelProcessor:
    """Process items in parallel with thread pool."""
    
    def __init__(self, max_workers: int = 5, timeout_seconds: float = 300.0):
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
    
    def process_items(
        self,
        items: List[Dict],
        processor_func: Callable[[Dict], Dict],
        item_id_key: str = "event_name"
    ) -> List[ProcessingResult]:
        """Process multiple items in parallel.
        
        Args:
            items: List of items to process
            processor_func: Function to process each item
            item_id_key: Key to use as item identifier
            
        Returns:
            List of processing results
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {}
            for item in items:
                item_id = item.get(item_id_key, str(id(item)))
                future = executor.submit(self._process_with_timeout, processor_func, item, item_id)
                future_to_item[future] = (item, item_id)
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                item, item_id = future_to_item[future]
                try:
                    result = future.result(timeout=self.timeout_seconds)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process {item_id}: {e}")
                    results.append(ProcessingResult(
                        item_id=item_id,
                        success=False,
                        result=None,
                        duration_ms=0.0,
                        error=str(e)
                    ))
        
        return results
    
    def _process_with_timeout(
        self,
        processor_func: Callable,
        item: Dict,
        item_id: str
    ) -> ProcessingResult:
        """Process a single item with timing."""
        start_time = time.time()
        
        try:
            result = processor_func(item)
            duration_ms = (time.time() - start_time) * 1000
            
            return ProcessingResult(
                item_id=item_id,
                success=True,
                result=result,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Error processing {item_id}: {e}")
            
            return ProcessingResult(
                item_id=item_id,
                success=False,
                result=None,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    def process_events_parallel(
        self,
        events: List[Dict],
        process_func: Callable[[Dict], Dict],
        description: str = "Processing events"
    ) -> List[Dict]:
        """Process events in parallel and return successful results.
        
        Args:
            events: List of events to process
            process_func: Function to process each event
            description: Description for logging
            
        Returns:
            List of successfully processed events
        """
        logger.info(f"{description}: {len(events)} events with {self.max_workers} workers")
        
        results = self.process_items(events, process_func)
        
        # Collect successful results
        successful = [r.result for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if failed:
            logger.warning(f"{len(failed)} events failed processing")
            for r in failed[:5]:  # Log first 5 failures
                logger.warning(f"  - {r.item_id}: {r.error}")
        
        # Log statistics
        total_duration = sum(r.duration_ms for r in results)
        avg_duration = total_duration / len(results) if results else 0
        logger.info(
            f"{description} complete: {len(successful)}/{len(events)} successful, "
            f"avg {avg_duration:.0f}ms per event"
        )
        
        return successful


class ParallelEventProcessor:
    """Specialized processor for event pipeline operations."""
    
    def __init__(self, max_workers: int = 5):
        self.processor = ParallelProcessor(max_workers=max_workers)
    
    def scrape_events_parallel(
        self,
        events: List[Dict],
        scraper_func: Callable[[Dict], Dict]
    ) -> List[Dict]:
        """Scrape multiple event websites in parallel."""
        return self.processor.process_events_parallel(
            events,
            scraper_func,
            description="Scraping event websites"
        )
    
    def qualify_events_parallel(
        self,
        events: List[Dict],
        qualification_func: Callable[[Dict], Dict]
    ) -> List[Dict]:
        """Qualify multiple events in parallel."""
        return self.processor.process_events_parallel(
            events,
            qualification_func,
            description="Qualifying events"
        )
    
    def analyze_intelligence_parallel(
        self,
        events: List[Dict],
        analysis_func: Callable[[Dict], Dict]
    ) -> List[Dict]:
        """Analyze intelligence for multiple events in parallel."""
        return self.processor.process_events_parallel(
            events,
            analysis_func,
            description="Analyzing event intelligence"
        )
    
    def generate_outreach_parallel(
        self,
        events: List[Dict],
        outreach_func: Callable[[Dict], Dict]
    ) -> List[Dict]:
        """Generate outreach emails for multiple events in parallel."""
        return self.processor.process_events_parallel(
            events,
            outreach_func,
            description="Generating outreach emails"
        )


def process_events_in_batches(
    events: List[Dict],
    process_func: Callable[[Dict], Dict],
    batch_size: int = 10,
    max_workers: int = 5
) -> List[Dict]:
    """Process events in batches with parallel processing within each batch.
    
    This is useful for very large event lists to manage memory.
    
    Args:
        events: List of events to process
        process_func: Function to process each event
        batch_size: Number of events per batch
        max_workers: Number of parallel workers
        
    Returns:
        List of all processed events
    """
    processor = ParallelProcessor(max_workers=max_workers)
    all_results = []
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(events) - 1)//batch_size + 1}")
        
        batch_results = processor.process_events_parallel(batch, process_func)
        all_results.extend(batch_results)
    
    return all_results


# Global processor instance
_parallel_processor: Optional[ParallelEventProcessor] = None


def get_parallel_processor(max_workers: int = 5) -> ParallelEventProcessor:
    """Get global parallel processor instance."""
    global _parallel_processor
    if _parallel_processor is None:
        _parallel_processor = ParallelEventProcessor(max_workers=max_workers)
    return _parallel_processor
