"""Fuzzy event deduplication utilities."""

import re
import logging
from difflib import SequenceMatcher
from urllib.parse import urlparse
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize URL for comparison.
    
    Removes protocol, www, trailing slashes, and query parameters.
    """
    if not url:
        return ""
    
    parsed = urlparse(url.lower())
    netloc = parsed.netloc
    
    # Remove www prefix
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    
    # Remove port if present
    if ':' in netloc:
        netloc = netloc.split(':')[0]
    
    path = parsed.path.rstrip('/')
    
    return f"{netloc}{path}"


def normalize_event_name(name: str) -> str:
    """Normalize event name for comparison.
    
    Lowercases, removes extra whitespace, and common suffixes.
    """
    if not name:
        return ""
    
    # Lowercase and strip
    name = name.lower().strip()
    
    # Remove common suffixes that vary
    suffixes = [
        r'\s+\d{4}$',  # Year at end
        r'\s+conference$',
        r'\s+summit$',
        r'\s+expo$',
        r'\s+forum$',
        r'\s+festival$',
    ]
    
    for suffix in suffixes:
        name = re.sub(suffix, '', name)
    
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate string similarity using SequenceMatcher.
    
    Returns a float between 0 and 1, where 1 is identical.
    """
    if not str1 or not str2:
        return 0.0
    
    return SequenceMatcher(None, str1, str2).ratio()


def is_duplicate_event(event1: Dict, event2: Dict, threshold: float = 0.85) -> bool:
    """Check if two events are duplicates.
    
    Compares by URL (exact match after normalization) or
    by name similarity (fuzzy match).
    """
    # Check URL match first (more reliable)
    url1 = normalize_url(event1.get('event_website', ''))
    url2 = normalize_url(event2.get('event_website', ''))
    
    if url1 and url2 and url1 == url2:
        return True
    
    # Check name similarity
    name1 = normalize_event_name(event1.get('event_name', ''))
    name2 = normalize_event_name(event2.get('event_name', ''))
    
    similarity = calculate_similarity(name1, name2)
    
    return similarity >= threshold


def has_more_complete_data(event1: Dict, event2: Dict) -> bool:
    """Determine which event has more complete data.
    
    Returns True if event1 has more data, False if event2 has more.
    """
    fields_to_check = [
        'start_date', 'end_date', 'city', 'country', 'organizer',
        'contact_email', 'summary', 'target_audience'
    ]
    
    score1 = sum(1 for f in fields_to_check if event1.get(f))
    score2 = sum(1 for f in fields_to_check if event2.get(f))
    
    return score1 >= score2


def deduplicate_events(events: List[Dict], threshold: float = 0.85) -> List[Dict]:
    """Remove duplicate events from a list.
    
    Keeps the event with more complete data when duplicates are found.
    
    Args:
        events: List of event dictionaries
        threshold: Similarity threshold (0-1) for fuzzy matching
        
    Returns:
        List of deduplicated events
    """
    if not events:
        return []
    
    deduplicated = []
    seen_indices = set()
    
    for i, event1 in enumerate(events):
        if i in seen_indices:
            continue
        
        best_event = event1
        
        for j, event2 in enumerate(events[i + 1:], start=i + 1):
            if j in seen_indices:
                continue
            
            if is_duplicate_event(event1, event2, threshold):
                # Keep the one with more complete data
                if has_more_complete_data(event2, best_event):
                    best_event = event2
                seen_indices.add(j)
                logger.info(
                    f"Merged duplicate events: '{event1.get('event_name')}' and "
                    f"'{event2.get('event_name')}'"
                )
        
        deduplicated.append(best_event)
    
    removed_count = len(events) - len(deduplicated)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} duplicate events")
    
    return deduplicated


def find_similar_events(event: Dict, events: List[Dict], threshold: float = 0.75) -> List[Dict]:
    """Find events similar to a given event.
    
    Useful for suggesting related events.
    
    Args:
        event: Reference event
        events: List of events to search
        threshold: Similarity threshold
        
    Returns:
        List of similar events
    """
    similar = []
    
    for other in events:
        if other is event:
            continue
        
        if is_duplicate_event(event, other, threshold):
            similar.append(other)
    
    return similar
