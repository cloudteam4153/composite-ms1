import asyncio
import logging
from typing import List, Callable, Any, Dict, Awaitable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools

logger = logging.getLogger(__name__)


async def execute_parallel(
    tasks: Sequence[Awaitable[Any]],
    max_workers: int = 5
) -> List[Any]:
    """
    Execute multiple async tasks in parallel using thread pool
    
    Args:
        tasks: List of async callable functions
        max_workers: Maximum number of worker threads
        
    Returns:
        List of results in the same order as tasks
    """
    if not tasks:
        return []
    
    logger.info(f"Executing {len(tasks)} tasks in parallel with {max_workers} workers")
    
    # Run async tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check for exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Task {i} failed: {str(result)}")
            raise result
    
    logger.info(f"Completed {len(tasks)} parallel tasks")
    return results


async def execute_parallel_with_timeout(
    tasks: List[Awaitable[Any]],
    timeout: float = 30.0,
    max_workers: int = 5
) -> List[Any]:
    """
    Execute multiple async tasks in parallel with timeout
    
    Args:
        tasks: List of async callable functions
        timeout: Maximum time to wait for all tasks
        max_workers: Maximum number of worker threads
        
    Returns:
        List of results in the same order as tasks
    """
    try:
        results = await asyncio.wait_for(
            execute_parallel(tasks, max_workers),
            timeout=timeout
        )
        return results
    except asyncio.TimeoutError:
        logger.error(f"Parallel execution timed out after {timeout} seconds")
        raise TimeoutError(f"Parallel execution timed out after {timeout} seconds")

