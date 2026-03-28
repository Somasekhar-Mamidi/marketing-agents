"""Vendor discovery agent with service provider search capabilities."""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from agents.base import BaseAgent, AgentInput, AgentOutput
from utils.search import WebSearchTool

logger = logging.getLogger(__name__)


SERVICE_CATEGORIES = {
    'booth_builder': {
        'keywords': ['booth builder', 'exhibition stand', 'stand contractor', 
                     'exhibition design', 'trade show booth', 'custom booth'],
        'search_queries': [
            '{location} exhibition stand builders',
            '{location} trade show booth contractors',
            '{location} custom booth design',
        ]
    },
    'av_equipment': {
        'keywords': ['av equipment', 'audio visual', 'stage design', 
                     'lighting rental', 'sound system'],
        'search_queries': [
            '{location} av equipment rental',
            '{location} audio visual services events',
        ]
    },
    'catering': {
        'keywords': ['event catering', 'corporate catering', 
                     'conference food service'],
        'search_queries': [
            '{location} event catering services',
            '{location} corporate event catering',
        ]
    },
    'printing': {
        'keywords': ['event printing', 'banner printing', 'signage', 
                     'promotional materials', 'large format printing'],
        'search_queries': [
            '{location} event banner printing',
            '{location} exhibition signage printing',
        ]
    },
    'logistics': {
        'keywords': ['event logistics', 'freight', 'shipping', 
                     'storage', 'installation services'],
        'search_queries': [
            '{location} event logistics services',
            '{location} exhibition freight forwarding',
        ]
    },
    'furniture_rental': {
        'keywords': ['event furniture', 'rental furniture', 
                     'booth furniture', 'display fixtures'],
        'search_queries': [
            '{location} event furniture rental',
            '{location} exhibition furniture hire',
        ]
    },
}


class VendorDiscoveryAgent(BaseAgent):
    """Discovers vendors and service providers for events."""
    
    name = "vendor_discovery"
    description = "Discovers vendors, sponsors, and service providers"
    
    def __init__(self, max_vendors_per_event: int = 10, search_service_providers: bool = True):
        self.search_tool = WebSearchTool(provider="auto")
        self.max_vendors_per_event = max_vendors_per_event
        self.search_service_providers = search_service_providers
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute vendor discovery."""
        self.validate_input(input_data)
        
        events = input_data.context.get("events", [])
        service_category = input_data.parameters.get('service_category')
        location = input_data.parameters.get('location')
        
        if not events and service_category and location:
            vendors = self._search_service_providers_directly(service_category, location)
            return AgentOutput(
                agent_name=self.name,
                findings={"vendors": vendors, "service_category": service_category, "location": location},
                metadata={"agent": self.name, "vendor_count": len(vendors), "search_type": "direct"}
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
            event_vendors = self._discover_vendors_for_event(event)
            all_vendors.extend(event_vendors)
            for vendor in event_vendors:
                vendor['event_id'] = event.get('id')
                vendor['event_name'] = event.get('event_name')
            
            if self.search_service_providers:
                location = f"{event.get('city', '')} {event.get('country', '')}".strip()
                if location:
                    service_providers = self._search_service_providers_for_event(
                        event.get('event_name', ''), location, service_category
                    )
                    all_vendors.extend(service_providers)
        
        logger.info(f"Discovered {len(all_vendors)} total vendors")
        
        return AgentOutput(
            agent_name=self.name,
            findings={"vendors": all_vendors, "events": events},
            metadata={"agent": self.name, "vendor_count": len(all_vendors), "events_processed": len(events)}
        )
    
    def _search_service_providers_directly(self, category: str, location: str) -> List[Dict]:
        """Search for service providers by category and location."""
        keywords = SERVICE_CATEGORIES.get(category, {}).get('keywords', [category])
        vendors = []
        
        for keyword in keywords[:2]:
            queries = [
                f"{keyword} {location}",
                f"{keyword} companies {location}",
                f"best {keyword} {location}",
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
        """Search for service providers for a specific event."""
        vendors = []
        
        if specific_category and specific_category in SERVICE_CATEGORIES:
            categories = {specific_category: SERVICE_CATEGORIES[specific_category]}
        else:
            categories = {
                'booth_builder': SERVICE_CATEGORIES['booth_builder'],
                'av_equipment': SERVICE_CATEGORIES['av_equipment'],
                'printing': SERVICE_CATEGORIES['printing']
            }
        
        for category, keywords in categories.items():
            for keyword in keywords['keywords'][:2]:
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
        """Parse search result into vendor dict."""
        title = result.get('title', '')
        url = result.get('url', '')
        content = result.get('content', '')
        
        if not title or not url:
            return None
        
        company_name = title.split('|')[0].split('-')[0].strip()
        company_name = company_name.split(':')[0].strip()
        
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
        """Check if vendor already exists in list."""
        vendor_name = vendor.get('vendor_name', '').lower()
        vendor_url = vendor.get('vendor_website', '').lower()
        
        for existing in existing_vendors:
            existing_name = existing.get('vendor_name', '').lower()
            existing_url = existing.get('vendor_website', '').lower()
            
            if vendor_name == existing_name:
                return True
            
            if vendor_url and existing_url:
                from urllib.parse import urlparse
                vendor_domain = urlparse(vendor_url).netloc.replace('www.', '')
                existing_domain = urlparse(existing_url).netloc.replace('www.', '')
                if vendor_domain == existing_domain:
                    return True
        
        return False
    
    def _discover_vendors_for_event(self, event: Dict) -> List[Dict]:
        """Discover vendors for a single event."""
        event_name = event.get('event_name', '')
        vendors = []
        
        past_sponsors = self._search_past_sponsors(event_name)
        vendors.extend(past_sponsors)
        
        current_sponsors = self._search_current_sponsors(event_name)
        vendors.extend(current_sponsors)
        
        exhibitors = self._search_exhibitors(event_name)
        vendors.extend(exhibitors)
        
        vendors = self._deduplicate_vendors(vendors)
        
        return vendors[:self.max_vendors_per_event]
    
    def _search_past_sponsors(self, event_name: str) -> List[Dict]:
        """Search for past sponsors."""
        query = f"{event_name} past sponsors previous years"
        try:
            results = self.search_tool.search(query, max_results=5)
            return [self._parse_vendor_result(r, 'sponsor') for r in results]
        except Exception as e:
            logger.error(f"Error searching past sponsors: {e}")
            return []
    
    def _search_current_sponsors(self, event_name: str) -> List[Dict]:
        """Search for current sponsors."""
        query = f"{event_name} sponsors 2024 2025"
        try:
            results = self.search_tool.search(query, max_results=5)
            return [self._parse_vendor_result(r, 'sponsor') for r in results]
        except Exception as e:
            logger.error(f"Error searching current sponsors: {e}")
            return []
    
    def _search_exhibitors(self, event_name: str) -> List[Dict]:
        """Search for exhibitors."""
        query = f"{event_name} exhibitors"
        try:
            results = self.search_tool.search(query, max_results=5)
            return [self._parse_vendor_result(r, 'exhibitor') for r in results]
        except Exception as e:
            logger.error(f"Error searching exhibitors: {e}")
            return []
    
    def _parse_vendor_result(self, result: Dict, vendor_type: str) -> Dict:
        """Parse vendor search result."""
        return {
            'vendor_name': result.get('title', '').split('|')[0].strip(),
            'vendor_website': result.get('url', ''),
            'vendor_type': vendor_type,
            'description': result.get('content', '')[:200],
            'source': 'search',
        }
    
    def _deduplicate_vendors(self, vendors: List[Dict]) -> List[Dict]:
        """Remove duplicate vendors."""
        seen = set()
        unique = []
        for v in vendors:
            name = v.get('vendor_name', '').lower()
            if name and name not in seen:
                seen.add(name)
                unique.append(v)
        return unique
