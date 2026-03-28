"""Vendor Discovery Agent - Discovers sponsors and exhibitors for events."""

import logging
from typing import List, Dict, Optional
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.search import WebSearchTool

logger = logging.getLogger(__name__)


class VendorDiscoveryAgent(BaseAgent):
    """Discovers vendors (sponsors, exhibitors, partners, service providers) for events.
    
    Searches for:
    - Past sponsors from previous editions
    - Current sponsors/exhibitors
    - Potential vendor contacts
    - Event service providers (booth builders, contractors, etc.)
    """
    
    name = "vendor_discovery"
    description = "Discovers vendors, sponsors, and service providers for events"
    
    VENDOR_TYPES = ['sponsor', 'exhibitor', 'partner', 'speaker', 'service_provider']
    
    # Service provider categories for event support
    SERVICE_CATEGORIES = {
        'booth_builder': ['booth builder', 'exhibition stand', 'stand contractor', 'exhibition design', 'trade show booth'],
        'av_equipment': ['av equipment', 'audio visual', 'stage design', 'lighting', 'sound system'],
        'catering': ['catering', 'food service', 'event catering', 'hospitality'],
        'printing': ['event printing', 'banner printing', 'signage', 'promotional materials'],
        'logistics': ['event logistics', 'freight', 'shipping', 'storage', 'installation'],
        'marketing': ['event marketing', 'promotion', 'social media', 'pr agency'],
        'technology': ['event technology', 'registration system', 'event app', 'virtual platform'],
        'security': ['event security', 'crowd management', 'safety'],
        'staffing': ['event staffing', 'hostess', 'promotional staff', 'interpreters'],
        'transportation': ['transportation', 'shuttle service', 'vip transport'],
        'venue': ['venue', 'conference center', 'exhibition hall', 'hotel venue'],
        'photography': ['event photography', 'videography', 'live streaming'],
        'furniture': ['event furniture', 'rental furniture', 'booth furniture', 'display fixtures'],
        'floral': ['event floral', 'decoration', 'staging', 'theme design']
    }
    
    def __init__(self, max_vendors_per_event: int = 10, search_service_providers: bool = True):
        self.search_tool = WebSearchTool(provider="auto")
        self.max_vendors_per_event = max_vendors_per_event
        self.search_service_providers = search_service_providers
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Discover vendors for events."""
        self.validate_input(input_data)
        
        events = input_data.context.get("events", [])
        
        # Check if specific service provider search is requested
        service_category = input_data.parameters.get('service_category', None)
        location = input_data.parameters.get('location', None)
        
        if not events and service_category and location:
            # Direct service provider search (no events)
            vendors = self._search_service_providers_directly(service_category, location)
            return AgentOutput(
                agent_name=self.name,
                findings={
                    "vendors": vendors,
                    "service_category": service_category,
                    "location": location
                },
                metadata={
                    "agent": self.name,
                    "vendor_count": len(vendors),
                    "search_type": "direct_service_provider"
                }
            )
        
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={"vendors": [], "message": "No events to process"},
                metadata={"agent": self.name, "vendor_count": 0}
            )
        
        logger.info(f"Discovering vendors for {len(events)} events")
        
        all_vendors = []
        
        for event in events:
            # Search for traditional vendors (sponsors/exhibitors)
            event_vendors = self._discover_vendors_for_event(event)
            all_vendors.extend(event_vendors)
            
            # Link vendors to event
            for vendor in event_vendors:
                vendor['event_id'] = event.get('id')
                vendor['event_name'] = event.get('event_name')
            
            # Search for service providers if enabled
            if self.search_service_providers:
                location = event.get('city', '') + ' ' + event.get('country', '')
                if location.strip():
                    service_providers = self._search_service_providers_for_event(
                        event.get('event_name', ''), 
                        location.strip(),
                        service_category
                    )
                    all_vendors.extend(service_providers)
        
        logger.info(f"Discovered {len(all_vendors)} total vendors")
        
        return AgentOutput(
            agent_name=self.name,
            findings={
                "vendors": all_vendors,
                "events": events
            },
            metadata={
                "agent": self.name,
                "vendor_count": len(all_vendors),
                "events_processed": len(events)
            }
        )
    
    def _search_service_providers_directly(self, category: str, location: str) -> List[Dict]:
        """Search for service providers directly by category and location.
        
        Args:
            category: Service category (e.g., 'booth_builder', 'catering')
            location: Location (e.g., 'Dublin, Ireland')
            
        Returns:
            List of vendor dictionaries
        """
        keywords = self.SERVICE_CATEGORIES.get(category, [category])
        vendors = []
        
        for keyword in keywords[:2]:  # Use top 2 keywords
            queries = [
                f"{keyword} {location}",
                f"{keyword} companies {location}",
                f"best {keyword} {location}",
                f"{keyword} services {location}"
            ]
            
            for query in queries:
                try:
                    results = self.search_tool.search(query, max_results=5)
                    for result in results:
                        vendor = self._parse_service_provider_result(result, category)
                        if vendor and not self._is_duplicate_vendor(vendor, vendors):
                            vendors.append(vendor)
                            
                    if len(vendors) >= self.max_vendors_per_event * 2:
                        break
                        
                except Exception as e:
                    logger.error(f"Error searching service providers: {e}")
                    continue
            
            if len(vendors) >= self.max_vendors_per_event * 2:
                break
        
        return vendors[:self.max_vendors_per_event * 2]
    
    def _search_service_providers_for_event(self, event_name: str, location: str, specific_category: Optional[str] = None) -> List[Dict]:
        """Search for service providers for a specific event.
        
        Args:
            event_name: Name of the event
            location: Event location
            specific_category: Optional specific category to search for
            
        Returns:
            List of vendor dictionaries
        """
        vendors = []
        
        # Determine which categories to search
        if specific_category and specific_category in self.SERVICE_CATEGORIES:
            categories = {specific_category: self.SERVICE_CATEGORIES[specific_category]}
        else:
            # Search for booth builders and key service providers by default
            categories = {
                'booth_builder': self.SERVICE_CATEGORIES['booth_builder'],
                'av_equipment': self.SERVICE_CATEGORIES['av_equipment'],
                'printing': self.SERVICE_CATEGORIES['printing']
            }
        
        for category, keywords in categories.items():
            for keyword in keywords[:2]:
                query = f"{keyword} {location}"
                
                try:
                    results = self.search_tool.search(query, max_results=3)
                    for result in results:
                        vendor = self._parse_service_provider_result(result, category)
                        if vendor and not self._is_duplicate_vendor(vendor, vendors):
                            vendor['event_name'] = event_name
                            vendor['vendor_type'] = 'service_provider'
                            vendor['service_category'] = category
                            vendors.append(vendor)
                            
                except Exception as e:
                    logger.error(f"Error searching {category}: {e}")
                    continue
                
                if len(vendors) >= self.max_vendors_per_event:
                    break
            
            if len(vendors) >= self.max_vendors_per_event:
                break
        
        return vendors[:self.max_vendors_per_event]
    
    def _parse_service_provider_result(self, result: Dict, category: str) -> Optional[Dict]:
        """Parse a search result into a service provider vendor dict.
        
        Args:
            result: Search result dict with 'title', 'url', 'content'
            category: Service category
            
        Returns:
            Vendor dict or None if parsing fails
        """
        title = result.get('title', '')
        url = result.get('url', '')
        content = result.get('content', '')
        
        if not title or not url:
            return None
        
        # Extract company name from title
        company_name = title.split('|')[0].split('-')[0].strip()
        company_name = company_name.split(':')[0].strip()
        
        # Clean up common suffixes
        suffixes = ['Home', 'Contact', 'About', 'Services', 'Ltd', 'Limited']
        for suffix in suffixes:
            if company_name.endswith(f' {suffix}'):
                company_name = company_name[:-len(suffix)-1].strip()
        
        return {
            'vendor_name': company_name,
            'vendor_website': url,
            'vendor_type': 'service_provider',
            'service_category': category,
            'source': 'search',
            'relevance_score': result.get('score', 0.5),
            'description': content[:200] if content else '',
            'contact_email': None,
            'contact_phone': None
        }
    
    def _is_duplicate_vendor(self, vendor: Dict, existing_vendors: List[Dict]) -> bool:
        """Check if vendor is already in list.
        
        Args:
            vendor: New vendor to check
            existing_vendors: List of existing vendors
            
        Returns:
            True if duplicate found
        """
        vendor_name = vendor.get('vendor_name', '').lower()
        vendor_url = vendor.get('vendor_website', '').lower()
        
        for existing in existing_vendors:
            existing_name = existing.get('vendor_name', '').lower()
            existing_url = existing.get('vendor_website', '').lower()
            
            # Check name similarity
            if vendor_name == existing_name:
                return True
            
            # Check URL similarity (normalize URLs)
            if vendor_url and existing_url:
                # Extract domain
                from urllib.parse import urlparse
                vendor_domain = urlparse(vendor_url).netloc.replace('www.', '')
                existing_domain = urlparse(existing_url).netloc.replace('www.', '')
                if vendor_domain == existing_domain:
                    return True
        
        return False
    
    def _search_current_sponsors(self, event_name: str) -> List[Dict]:
        """Search for current sponsors."""
        query = f"{event_name} 2025 sponsors partners"
        
        try:
            results = self.search_tool.search(query, max_results=5)
            vendors = []
            
            for result in results:
                vendor = self._extract_vendor_from_result(result, 'sponsor')
                if vendor:
                    vendors.append(vendor)
            
            return vendors
        except Exception as e:
            logger.warning(f"Failed to search current sponsors for {event_name}: {e}")
            return []
    
    def _search_exhibitors(self, event_name: str) -> List[Dict]:
        """Search for exhibitors."""
        query = f"{event_name} exhibitors 2025"
        
        try:
            results = self.search_tool.search(query, max_results=5)
            vendors = []
            
            for result in results:
                vendor = self._extract_vendor_from_result(result, 'exhibitor')
                if vendor:
                    vendors.append(vendor)
            
            return vendors
        except Exception as e:
            logger.warning(f"Failed to search exhibitors for {event_name}: {e}")
            return []
    
    def _extract_vendor_from_result(self, result: Dict, vendor_type: str) -> Optional[Dict]:
        """Extract vendor information from search result."""
        title = result.get('title', '')
        url = result.get('url', '')
        content = result.get('content', '')
        
        # Basic extraction - in production, use NLP/LLM
        # For now, extract company names from title
        vendor_name = self._extract_company_name(title)
        
        if not vendor_name:
            return None
        
        return {
            'vendor_name': vendor_name,
            'vendor_type': vendor_type,
            'vendor_website': url,
            'source': title,
            'relevance_score': 0,  # To be calculated by profiling agent
            'status': 'identified'
        }
    
    def _extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name from text."""
        # Remove common suffixes/prefixes
        clean = text.replace('Sponsored by', '').replace('Partner:', '')
        clean = clean.replace('Exhibitor:', '').replace('|', ' ')
        
        # Take first reasonable segment
        parts = clean.split()
        if len(parts) >= 2:
            return ' '.join(parts[:3])  # First 2-3 words
        
        return None
    
    def _deduplicate_vendors(self, vendors: List[Dict]) -> List[Dict]:
        """Remove duplicate vendors."""
        seen = set()
        unique = []
        
        for vendor in vendors:
            name = vendor.get('vendor_name', '').lower().strip()
            if name and name not in seen:
                seen.add(name)
                unique.append(vendor)
        
        return unique
