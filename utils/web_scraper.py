"""Advanced web scraping utilities for event website extraction."""

import logging
import re
from typing import Optional, Tuple, List
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EventWebsiteScraper:
    """Scrapes event websites to extract structured information."""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            follow_redirects=True
        )
    
    def scrape_event_page(self, url: str) -> dict:
        """Scrape an event page and extract structured information.
        
        Args:
            url: The event website URL
            
        Returns:
            Dictionary with extracted event information
        """
        result = {
            "start_date": None,
            "end_date": None,
            "city": None,
            "country": None,
            "organizer": None,
            "contact_email": None,
            "contact_url": None,
            "sponsorship_url": None,
            "summary": None,
            "industry_focus": None,
            "target_audience": None,
            "technology_themes": None,
            "scraped_successfully": False,
            "error": None
        }
        
        try:
            logger.info(f"Scraping event page: {url}")
            response = self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract dates
            start_date, end_date = self._extract_dates(soup, response.text)
            result["start_date"] = start_date
            result["end_date"] = end_date
            
            # Extract location
            city, country = self._extract_location(soup, response.text)
            result["city"] = city
            result["country"] = country
            
            # Extract organizer
            result["organizer"] = self._extract_organizer(soup, response.text)
            
            # Extract contact information
            result["contact_email"] = self._extract_email(response.text)
            result["contact_url"] = self._extract_contact_url(soup, url)
            result["sponsorship_url"] = self._extract_sponsorship_url(soup, url)
            
            # Extract descriptions
            result["summary"] = self._extract_summary(soup)
            result["target_audience"] = self._extract_target_audience(soup, response.text)
            result["industry_focus"] = self._extract_industry_focus(soup, response.text)
            result["technology_themes"] = self._extract_themes(soup, response.text)
            
            result["scraped_successfully"] = True
            logger.info(f"Successfully scraped {url}")
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            result["error"] = str(e)
        
        return result
    
    def _extract_dates(self, soup: BeautifulSoup, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract event dates from the page."""
        dates = {"start": None, "end": None}
        
        # Try JSON-LD structured data first (most reliable)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') in ['Event', 'BusinessEvent']:
                        dates["start"] = data.get('startDate')
                        dates["end"] = data.get('endDate')
                        break
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Try meta tags
        if not dates["start"]:
            meta_start = soup.find('meta', {'property': 'event:start_time'})
            if meta_start:
                dates["start"] = meta_start.get('content')
            
            meta_end = soup.find('meta', {'property': 'event:end_time'})
            if meta_end:
                dates["end"] = meta_end.get('content')
        
        # Try common date patterns in text
        if not dates["start"]:
            date_patterns = [
                # Month Day, Year - Month Day, Year
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s*[-–]\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})',
                # Month Day-Day, Year
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s*[-–]\s*(\d{1,2}),?\s*(\d{4})',
                # Month Day, Year
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})',
                # DD/MM/YYYY or DD-MM-YYYY
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
                # ISO format
                r'(\d{4}-\d{2}-\d{2})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    dates["start"] = match.group(0)
                    break
        
        return dates["start"], dates["end"]
    
    def _extract_location(self, soup: BeautifulSoup, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract city and country from the page."""
        city = None
        country = None
        
        # Try JSON-LD location data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') in ['Event', 'BusinessEvent']:
                    location = data.get('location', {})
                    if isinstance(location, dict):
                        address = location.get('address', {})
                        if isinstance(address, dict):
                            city = address.get('addressLocality')
                            country = address.get('addressCountry')
                        if not city:
                            city = location.get('name')
            except (json.JSONDecodeError, AttributeError):
                continue

        # Try common location patterns
        if not city or not country:
            # Pattern: "City, Country" or "City, State, Country"
            location_patterns = [
                r'(?:Location|Venue|Address)[:\s]+([^,]+),\s*([^,]+)(?:,\s*([^\n<]+))?',
                r'(?:in|at)\s+([A-Z][a-zA-Z\s]+),\s*([A-Z][a-zA-Z\s]+)',
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    if len(groups) >= 2:
                        city = groups[0].strip()
                        country = groups[-1].strip() if len(groups) > 2 else groups[1].strip()
                    break
        
        return city, country
    
    def _extract_organizer(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract event organizer from the page."""
        # Try JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') in ['Event', 'BusinessEvent']:
                    organizer = data.get('organizer', {})
                    if isinstance(organizer, dict):
                        return organizer.get('name')
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Try common patterns
        organizer_patterns = [
            r'(?:Organized by|Hosted by|Brought to you by)[:\s]+([^<\n]+)',
            r'(?:organizer|host)[:\s]+([^<\n]+)',
        ]
        
        for pattern in organizer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract contact email from the page."""
        # Look for email patterns
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        matches = re.findall(email_pattern, text)
        
        # Filter out common false positives
        filtered = [
            email for email in matches
            if not any(x in email.lower() for x in ['example', 'test', 'noreply', 'no-reply', 'sentry'])
        ]
        
        return filtered[0] if filtered else None
    
    def _extract_contact_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract contact page URL."""
        contact_keywords = ['contact', 'contact-us', 'get-in-touch', 'reach-out']
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text(strip=True).lower()
            
            if any(keyword in href or keyword in text for keyword in contact_keywords):
                return urljoin(base_url, link['href'])
        
        return None
    
    def _extract_sponsorship_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract sponsorship page URL."""
        sponsor_keywords = ['sponsor', 'sponsorship', 'partner', 'exhibit', 'become-sponsor']
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text(strip=True).lower()
            
            if any(keyword in href or keyword in text for keyword in sponsor_keywords):
                return urljoin(base_url, link['href'])
        
        return None
    
    def _extract_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract event summary/description."""
        # Try meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            return meta_desc.get('content')
        
        meta_og = soup.find('meta', {'property': 'og:description'})
        if meta_og:
            return meta_og.get('content')
        
        # Try first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text(strip=True)
            if len(text) > 50:
                return text[:500]
        
        return None
    
    def _extract_target_audience(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract target audience information."""
        audience_keywords = [
            'developer', 'engineer', 'cto', 'architect', 'manager',
            'executive', 'founder', 'entrepreneur', 'investor',
            'data scientist', 'analyst', 'designer', 'product'
        ]
        
        # Look for audience section
        audience_section = None
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            if 'audience' in heading.get_text(strip=True).lower():
                audience_section = heading.find_next(['p', 'ul', 'div'])
                break
        
        if audience_section:
            return audience_section.get_text(strip=True)[:300]
        
        # Try to find in text
        for keyword in audience_keywords:
            pattern = rf'{keyword}s?(?:\s+and\s+\w+)?'
            if re.search(pattern, text, re.IGNORECASE):
                return f"Target audience includes: {keyword}s"
        
        return None
    
    def _extract_industry_focus(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract industry focus."""
        industries = [
            'fintech', 'payments', 'artificial intelligence', 'ai', 'machine learning',
            'blockchain', 'cryptocurrency', 'healthcare', 'e-commerce', 'retail',
            'cybersecurity', 'cloud computing', 'devops', 'data science'
        ]
        
        found_industries = []
        for industry in industries:
            if re.search(rf'\b{industry}\b', text, re.IGNORECASE):
                found_industries.append(industry.title())
        
        return ', '.join(found_industries) if found_industries else None
    
    def _extract_themes(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract technology themes/topics."""
        themes = [
            'api', 'microservices', 'cloud', 'kubernetes', 'docker', 'aws',
            'security', 'privacy', 'scalability', 'performance', 'ux', 'ui',
            'mobile', 'web', 'backend', 'frontend', 'full-stack', 'database'
        ]
        
        found_themes = []
        for theme in themes:
            if re.search(rf'\b{theme}\b', text, re.IGNORECASE):
                found_themes.append(theme.title())
        
        return ', '.join(found_themes) if found_themes else None
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
