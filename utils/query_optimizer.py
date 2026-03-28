"""Search query optimization utilities."""

import re
import logging
from typing import List, Set, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Optimizes search queries to reduce redundancy and improve efficiency."""
    
    def __init__(self):
        self.query_history: Set[str] = set()
    
    def deduplicate_queries(self, queries: List[str]) -> List[str]:
        """Remove duplicate and near-duplicate queries.
        
        Args:
            queries: List of search queries
            
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for query in queries:
            # Normalize for comparison
            normalized = self._normalize_query(query)
            
            if normalized not in seen:
                seen.add(normalized)
                unique.append(query)
            else:
                logger.debug(f"Removed duplicate query: {query}")
        
        return unique
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for deduplication comparison."""
        # Lowercase, remove extra whitespace
        normalized = query.lower().strip()
        # Remove punctuation differences
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized
    
    def batch_similar_queries(self, queries: List[str], batch_size: int = 5) -> List[List[str]]:
        """Group similar queries for efficient batch processing.
        
        Args:
            queries: List of queries
            batch_size: Maximum queries per batch
            
        Returns:
            List of query batches
        """
        # Group by common terms
        groups = defaultdict(list)
        
        for query in queries:
            # Extract key terms (industry, region)
            terms = self._extract_key_terms(query)
            group_key = tuple(sorted(terms))
            groups[group_key].append(query)
        
        # Flatten into batches
        batches = []
        current_batch = []
        
        for group_queries in groups.values():
            for query in group_queries:
                current_batch.append(query)
                if len(current_batch) >= batch_size:
                    batches.append(current_batch)
                    current_batch = []
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _extract_key_terms(self, query: str) -> Set[str]:
        """Extract key terms from a query."""
        # Common industry terms
        industries = [
            'payments', 'fintech', 'ai', 'artificial intelligence', 'technology',
            'software', 'blockchain', 'cloud', 'cybersecurity', 'data'
        ]
        
        # Common region terms
        regions = [
            'usa', 'europe', 'apac', 'asia', 'india', 'singapore', 'dubai',
            'london', 'new york', 'germany', 'france', 'brazil'
        ]
        
        query_lower = query.lower()
        terms = set()
        
        for industry in industries:
            if industry in query_lower:
                terms.add(industry)
        
        for region in regions:
            if region in query_lower:
                terms.add(region)
        
        return terms
    
    def optimize_query(self, query: str) -> str:
        """Optimize a single query for better results.
        
        Args:
            query: Original query
            
        Returns:
            Optimized query
        """
        # Remove redundant words
        redundant = ['the', 'a', 'an', 'and', 'or', 'but']
        words = query.split()
        words = [w for w in words if w.lower() not in redundant]
        
        # Ensure year is present for events
        optimized = ' '.join(words)
        if not any(year in optimized for year in ['2024', '2025', '2026']):
            optimized += " 2025 2026"
        
        return optimized
    
    def generate_optimized_queries(
        self,
        industry: str,
        region: str = "",
        theme: str = "",
        max_queries: int = 20
    ) -> List[str]:
        """Generate optimized search queries.
        
        Args:
            industry: Industry focus
            region: Target region (optional)
            theme: Specific theme (optional)
            max_queries: Maximum number of queries to generate
            
        Returns:
            List of optimized queries
        """
        base_terms = [
            f"{industry} conference",
            f"{industry} summit",
            f"{industry} expo",
            f"{industry} forum",
            f"{industry} festival",
        ]
        
        if theme:
            base_terms.extend([
                f"{theme} conference",
                f"{theme} summit",
                f"{industry} {theme} event",
            ])
        
        # Add year to all queries
        queries = []
        for term in base_terms:
            queries.append(f"{term} 2025 2026")
        
        # Add regional variants
        if region:
            regional_queries = []
            for query in queries[:5]:  # Limit regional variants
                regional_queries.append(f"{query} {region}")
            queries.extend(regional_queries)
        else:
            # Add major regions
            regions = ["USA", "Europe", "APAC", "Singapore", "Dubai"]
            for r in regions[:3]:
                queries.append(f"{industry} conference 2025 2026 {r}")
        
        # Deduplicate and limit
        queries = self.deduplicate_queries(queries)
        return queries[:max_queries]
    
    def track_executed_query(self, query: str):
        """Track that a query was executed."""
        self.query_history.add(self._normalize_query(query))
    
    def was_query_executed(self, query: str) -> bool:
        """Check if a query was already executed."""
        return self._normalize_query(query) in self.query_history
    
    def get_query_stats(self) -> Dict:
        """Get statistics about executed queries."""
        return {
            "total_unique_queries": len(self.query_history),
            "queries": list(self.query_history)[:10]  # Sample
        }


class SearchResultDeduplicator:
    """Deduplicates search results to avoid processing same URLs multiple times."""
    
    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_titles: Set[str] = set()
    
    def is_duplicate(self, result: Dict) -> bool:
        """Check if result is a duplicate."""
        url = result.get('url', '').lower().strip()
        title = result.get('title', '').lower().strip()
        
        # Normalize URL
        url = self._normalize_url(url)
        
        if url in self.seen_urls:
            return True
        
        if title in self.seen_titles:
            return True
        
        return False
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Remove www
        url = re.sub(r'^www\.', '', url)
        # Remove trailing slash
        url = url.rstrip('/')
        return url
    
    def add_result(self, result: Dict):
        """Add result to tracking."""
        url = result.get('url', '').lower().strip()
        title = result.get('title', '').lower().strip()
        
        self.seen_urls.add(self._normalize_url(url))
        self.seen_titles.add(title)
    
    def filter_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Filter duplicate results from a list."""
        unique = []
        
        for result in results:
            if not self.is_duplicate(result):
                unique.append(result)
                self.add_result(result)
        
        duplicates_removed = len(results) - len(unique)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate search results")
        
        return unique


# Global instances
_query_optimizer: QueryOptimizer = None
_result_deduplicator: SearchResultDeduplicator = None


def get_query_optimizer() -> QueryOptimizer:
    """Get global query optimizer instance."""
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer()
    return _query_optimizer


def get_result_deduplicator() -> SearchResultDeduplicator:
    """Get global result deduplicator instance."""
    global _result_deduplicator
    if _result_deduplicator is None:
        _result_deduplicator = SearchResultDeduplicator()
    return _result_deduplicator
