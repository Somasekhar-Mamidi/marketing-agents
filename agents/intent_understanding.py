"""Intent Understanding Agent - Analyzes user requirements before event discovery."""

import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


@dataclass
class UserIntent:
    """Structured representation of user intent."""
    primary_goal: str
    industry: str
    sub_industries: List[str]
    regions: List[str]
    event_types: List[str]
    date_range: Dict[str, str]
    audience_target: Dict[str, any]
    sponsorship_budget: Optional[str]
    strategic_objectives: List[str]
    excluded_keywords: List[str]
    priority_signals: Dict[str, int]
    search_queries: List[str]
    quality_requirements: Dict[str, any]


class IntentUnderstandingAgent(BaseAgent):
    """Analyzes user input to extract structured intent and requirements.
    
    This agent sits between Schema Init and Event Discovery to:
    1. Parse natural language queries into structured parameters
    2. Understand implicit requirements (audience, budget, timing)
    3. Generate optimized search queries
    4. Define quality thresholds for event selection
    """
    
    name = "intent_understanding"
    description = "Analyzes user requirements and extracts structured search parameters"
    
    # Industry taxonomy for better matching (EXTENSIBLE - supports ANY industry)
    INDUSTRY_KEYWORDS = {
        # Financial services
        "fintech": ["fintech", "financial technology", "digital banking", "payments"],
        "payments": ["payments", "payment processing", "digital payments", "merchant services"],
        "banking": ["banking", "retail banking", "commercial banking", "neobank"],
        "insurtech": ["insurtech", "insurance technology", "digital insurance"],
        "wealthtech": ["wealthtech", "wealth management", "robo-advisor"],
        "regtech": ["regtech", "regulatory technology", "compliance"],
        # Technology
        "ai": ["ai", "artificial intelligence", "machine learning", "ml", "generative ai"],
        "crypto": ["crypto", "cryptocurrency", "blockchain", "web3", "defi"],
        "cybersecurity": ["cybersecurity", "infosec", "data security", "threat detection"],
        "cloud": ["cloud computing", "saas", "paas", "iaas", "serverless"],
        "devops": ["devops", "ci/cd", "infrastructure", "sre", "platform engineering"],
        "data": ["data science", "big data", "analytics", "data engineering", "bi"],
        # Other industries
        "healthcare": ["healthcare", "medtech", "digital health", "telemedicine"],
        "retail": ["retail", "e-commerce", "omnichannel", "retailtech"],
        "travel": ["travel", "tourism", "hospitality", "airlines", "hotels"],
        "transportation": ["transportation", "logistics", "supply chain", "mobility"],
        "energy": ["energy", "cleantech", "renewable", "sustainability", "climate"],
        "education": ["education", "edtech", "e-learning", "training"],
        "media": ["media", "entertainment", "streaming", "content", "gaming"],
        "telecom": ["telecom", "telecommunications", "5g", "connectivity"],
        "manufacturing": ["manufacturing", "industry 4.0", "automation", "iot"],
        "real_estate": ["real estate", "proptech", "property", "construction"],
        "agriculture": ["agriculture", "agtech", "farming", "foodtech"],
        "legal": ["legal", "legaltech", "law", "compliance"],
        "human_resources": ["hr", "human resources", "hrtech", "talent"],
        "marketing": ["marketing", "martech", "advertising", "adtech"],
        "sports": ["sports", "fitness", "wellness", "esports"],
    }
    
    # Event type taxonomy
    EVENT_TYPES = {
        "conference": ["conference", "summit", "convention", "symposium"],
        "exhibition": ["expo", "exhibition", "trade show", "fair"],
        "forum": ["forum", "roundtable", "dialogue"],
        "festival": ["festival", "week", "days"],
        "workshop": ["workshop", "bootcamp", "training", "masterclass"],
        "networking": ["meetup", "networking", "mixer", "social"],
    }
    
    # Regional mappings (EXTENSIBLE - supports ANY region)
    REGIONS = {
        # North America
        "usa": ["usa", "us", "united states", "america"],
        "canada": ["canada", "toronto", "vancouver", "montreal"],
        # Europe
        "europe": ["europe", "eu"],
        "uk": ["uk", "united kingdom", "london", "manchester", "birmingham"],
        "germany": ["germany", "berlin", "munich", "frankfurt", "hamburg"],
        "france": ["france", "paris", "lyon", "marseille"],
        "netherlands": ["netherlands", "amsterdam", "rotterdam"],
        "ireland": ["ireland", "dublin", "cork", "galway"],
        "spain": ["spain", "madrid", "barcelona", "valencia"],
        "italy": ["italy", "milan", "rome", "venice"],
        "switzerland": ["switzerland", "zurich", "geneva"],
        "nordics": ["nordics", "sweden", "norway", "denmark", "finland", "stockholm", "oslo", "copenhagen"],
        # Asia Pacific
        "apac": ["apac", "asia pacific"],
        "singapore": ["singapore"],
        "hong_kong": ["hong kong"],
        "japan": ["japan", "tokyo", "osaka"],
        "australia": ["australia", "sydney", "melbourne"],
        "india": ["india", "mumbai", "bangalore", "delhi", "hyderabad", "chennai", "pune"],
        "china": ["china", "beijing", "shanghai", "shenzhen"],
        "south_korea": ["south korea", "korea", "seoul"],
        # Middle East & Africa
        "middle_east": ["middle east", "gcc"],
        "uae": ["uae", "dubai", "abu dhabi"],
        "saudi_arabia": ["saudi arabia", "riyadh", "jeddah"],
        "israel": ["israel", "tel aviv", "jerusalem"],
        "africa": ["africa"],
        "south_africa": ["south africa", "cape town", "johannesburg"],
        "nigeria": ["nigeria", "lagos"],
        # Latin America
        "latam": ["latam", "latin america"],
        "brazil": ["brazil", "sao paulo", "rio de janeiro"],
        "mexico": ["mexico", "mexico city"],
        "argentina": ["argentina", "buenos aires"],
        # Global
        "global": ["global", "worldwide", "international"],
    }
    
    # Audience signals
    AUDIENCE_SIGNALS = {
        "executives": ["c-suite", "executive", "ceo", "cto", "cfo", "vp", "director"],
        "decision_makers": ["decision maker", "budget holder", "purchasing", "procurement"],
        "technical": ["developer", "engineer", "technical", "architect", "cto"],
        "business": ["business", "strategy", "product", "marketing", "sales"],
        "startups": ["startup", "founder", "entrepreneur", "scale-up"],
        "enterprise": ["enterprise", "fortune 500", "large company", "corporate"],
    }
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Analyze user input and extract structured intent."""
        self.validate_input(input_data)

        query = input_data.query.lower()
        params = input_data.parameters

        self.emit_thinking("searching", f"Analyzing query: '{input_data.query}'")
        logger.info(f"Analyzing intent for query: {query}")

        llm_intent = self._extract_intent_with_llm(query, params)
        
        if llm_intent:
            self.emit_thinking("result", f"LLM extracted intent — Industry: {llm_intent.industry}, Regions: {llm_intent.regions}")
            logger.info("Using LLM-extracted intent")
            intent = llm_intent
            search_queries = intent.search_queries
        else:
            self.emit_thinking("fallback", "LLM intent extraction failed, using rule-based extraction")
            logger.info("Falling back to rule-based intent extraction")
            industry = self._extract_industry(query, params)
            regions = self._extract_regions(query, params)
            event_types = self._extract_event_types(query)
            date_range = self._extract_date_range(query, params)
            audience = self._extract_audience_target(query)
            objectives = self._extract_objectives(query)

            search_queries = self._generate_search_queries(
                industry, regions, event_types, date_range, query
            )

            quality_requirements = self._define_quality_requirements(query, audience)

            self.emit_thinking("result", f"Detected industry: {industry['primary']}, regions: {regions}")

            intent = UserIntent(
                primary_goal=self._determine_primary_goal(query, objectives),
                industry=industry["primary"],
                sub_industries=industry["related"],
                regions=regions,
                event_types=event_types,
                date_range=date_range,
                audience_target=audience,
                sponsorship_budget=self._extract_budget_hints(query),
                strategic_objectives=objectives,
                excluded_keywords=self._extract_exclusions(query),
                priority_signals=self._calculate_priorities(query, audience, objectives),
                search_queries=search_queries,
                quality_requirements=quality_requirements
            )

        self.emit_thinking("result", f"Generated {len(search_queries)} search queries, confidence: {self._calculate_confidence(intent):.0%}")
        logger.info(f"Intent extracted: Industry={intent.industry}, "
                   f"Regions={intent.regions}, EventTypes={intent.event_types}")
        
        return AgentOutput(
            agent_name=self.name,
            findings={
                "intent": self._intent_to_dict(intent),
                "original_query": input_data.query,
                "interpretation_confidence": self._calculate_confidence(intent)
            },
            metadata={
                "agent": self.name,
                "search_query_count": len(search_queries),
                "industry_detected": intent.industry,
                "regions_detected": len(intent.regions)
            }
        )
    
    def _extract_industry(self, query: str, params: Dict) -> Dict[str, any]:
        """Extract primary and related industries from query - supports ANY industry."""
        primary = params.get("industry", "").lower().strip()
        related = []
        
        if primary:
            for industry, keywords in self.INDUSTRY_KEYWORDS.items():
                if primary == industry or any(kw == primary for kw in keywords):
                    primary = industry
                    break
        else:
            for industry, keywords in self.INDUSTRY_KEYWORDS.items():
                if any(kw in query for kw in keywords):
                    if not primary:
                        primary = industry
                    elif industry != primary:
                        related.append(industry)
        
        if not primary:
            words = query.split()
            for word in words:
                if len(word) > 3 and word not in ["events", "conference", "summit", "find", "search"]:
                    primary = word
                    break
        
        if not primary:
            primary = "general"
        
        return {
            "primary": primary,
            "related": list(set(related))[:3],
            "keywords": self.INDUSTRY_KEYWORDS.get(primary, [primary])
        }
    
    def _extract_regions(self, query: str, params: Dict) -> List[str]:
        """Extract target regions from query - supports ANY region."""
        regions = []
        
        # Check for explicit region parameter first
        if params.get("region"):
            region_param = params["region"].lower().strip()
            regions.append(region_param)
            
            # Check if it matches known regions
            for region, keywords in self.REGIONS.items():
                if region_param == region or any(kw == region_param for kw in keywords):
                    if region not in regions:
                        regions.append(region)
        
        # Check query for region keywords
        for region, keywords in self.REGIONS.items():
            if any(kw in query for kw in keywords):
                if region not in regions:
                    regions.append(region)
        
        # If still no regions found, try to extract city/country from query
        if not regions:
            # Extract potential location words
            location_words = []
            exclude_words = ["events", "conference", "summit", "find", "search", "industry"]
            words = query.split()
            for word in words:
                word_clean = word.strip(",").lower()
                if len(word_clean) > 3 and word_clean not in exclude_words:
                    # Capitalized words often indicate proper nouns (locations)
                    if word[0].isupper() or word_clean in ["ireland", "dublin", "london", "paris"]:
                        location_words.append(word_clean)
            
            if location_words:
                regions = location_words
        
        if not regions:
            regions = ["global"]
        
        return regions[:3]
    
    def _extract_event_types(self, query: str) -> List[str]:
        """Extract preferred event types from query."""
        types = []
        
        for event_type, keywords in self.EVENT_TYPES.items():
            if any(kw in query for kw in keywords):
                types.append(event_type)
        
        # Default to conference if no specific type mentioned
        if not types:
            types = ["conference", "summit", "exhibition"]
        
        return types[:3]
    
    def _extract_date_range(self, query: str, params: Dict) -> Dict[str, str]:
        """Extract target date range from query."""
        import re
        from datetime import datetime
        
        current_year = datetime.now().year
        
        # Look for quarter references
        quarter_match = re.search(r'q([1-4])\s*(\d{4})?', query, re.IGNORECASE)
        if quarter_match:
            quarter = int(quarter_match.group(1))
            year = int(quarter_match.group(2)) if quarter_match.group(2) else current_year + 1
            return {
                "type": "quarter",
                "quarter": quarter,
                "year": year,
                "start": f"{year}-{((quarter-1)*3)+1:02d}-01",
                "end": f"{year}-{quarter*3:02d}-30",
                "flexibility": "exact"
            }
        
        # Look for specific year
        year_match = re.search(r'\b(20\d{2})\b', query)
        if year_match:
            year = int(year_match.group(1))
            return {
                "type": "year",
                "year": year,
                "start": f"{year}-01-01",
                "end": f"{year}-12-31",
                "flexibility": "within_year"
            }
        
        # Look for relative timeframes
        if "next quarter" in query or "upcoming" in query:
            return {
                "type": "upcoming",
                "months": 6,
                "flexibility": "flexible"
            }
        
        # Default: next 12 months
        return {
            "type": "default",
            "months": 12,
            "start": f"{current_year}-01-01",
            "end": f"{current_year + 1}-12-31",
            "flexibility": "flexible"
        }
    
    def _extract_audience_target(self, query: str) -> Dict[str, any]:
        """Extract target audience characteristics."""
        audience = {
            "seniority_levels": [],
            "roles": [],
            "company_types": [],
            "company_size": "any",
            "geographic_focus": []
        }
        
        # Check for seniority signals
        for level, keywords in self.AUDIENCE_SIGNALS.items():
            if any(kw in query for kw in keywords):
                audience["seniority_levels"].append(level)
        
        # Default to decision-makers if no specific audience
        if not audience["seniority_levels"]:
            audience["seniority_levels"] = ["decision_makers", "executives"]
        
        # Extract company size hints
        if "enterprise" in query or "large" in query:
            audience["company_size"] = "enterprise"
        elif "startup" in query or "smb" in query:
            audience["company_size"] = "startup"
        elif "mid-market" in query or "mid size" in query:
            audience["company_size"] = "mid_market"
        
        return audience
    
    def _extract_objectives(self, query: str) -> List[str]:
        """Extract strategic objectives from query."""
        objectives = []
        
        objective_signals = {
            "lead_generation": ["leads", "prospects", "sales", "pipeline", "customers"],
            "brand_awareness": ["brand", "awareness", "visibility", "presence", "marketing"],
            "thought_leadership": ["speak", "present", "thought leader", "expert", "keynote"],
            "partnerships": ["partner", "alliance", "collaboration", "integration"],
            "recruitment": ["hire", "talent", "recruit", "engineers", "sales people"],
            "competitive_intelligence": ["competitors", "market intelligence", "competitive"],
            "product_launch": ["launch", "announce", "unveil", "release"],
        }
        
        for objective, keywords in objective_signals.items():
            if any(kw in query for kw in keywords):
                objectives.append(objective)
        
        # Default to lead generation
        if not objectives:
            objectives = ["lead_generation", "brand_awareness"]
        
        return objectives[:3]
    
    def _generate_search_queries(self, industry: Dict, regions: List, 
                                 event_types: List, date_range: Dict, 
                                 original_query: str) -> List[str]:
        """Generate optimized search queries based on extracted intent."""
        queries = []
        
        primary_ind = industry["primary"]
        year = date_range.get("year", 2026)
        
        # High-intent queries (specific combinations)
        for region in regions[:2]:  # Top 2 regions
            for event_type in event_types[:2]:  # Top 2 event types
                queries.append(f"{primary_ind} {event_type} {region} {year}")
        
        # Broader queries for coverage
        queries.append(f"{primary_ind} conference summit {year}")
        queries.append(f"{primary_ind} industry events {year}")
        
        # Include related industries for expansion
        for related in industry["related"][:2]:
            queries.append(f"{related} conference {year}")
        
        # Add original query variations
        queries.append(original_query)
        queries.append(f"{original_query} {year}")
        
        # Remove duplicates and limit
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower()
            if q_lower not in seen and len(q_lower) > 10:
                seen.add(q_lower)
                unique_queries.append(q)
        
        return unique_queries[:15]  # Max 15 queries
    
    def _define_quality_requirements(self, query: str, audience: Dict) -> Dict[str, any]:
        """Define minimum quality thresholds for event selection."""
        requirements = {
            "min_attendees": 100,
            "preferred_audience_seniority": audience["seniority_levels"],
            "must_have_website": True,
            "date_verification_required": True,
            "relevance_threshold": 0.6,
            "speaker_quality_preference": "industry_leaders" in query or "keynote" in query,
            "sponsorship_opportunities_required": True
        }
        
        # Adjust thresholds based on query signals
        if "enterprise" in query or "large" in query:
            requirements["min_attendees"] = 500
        elif "startup" in query:
            requirements["min_attendees"] = 50
            requirements["preferred_audience_seniority"] = ["founders", "startups"]
        
        if "premium" in query or "top tier" in query:
            requirements["relevance_threshold"] = 0.8
        
        return requirements
    
    def _determine_primary_goal(self, query: str, objectives: List[str]) -> str:
        """Determine the primary goal from objectives."""
        if objectives:
            return objectives[0].replace("_", " ").title()
        return "Event Discovery"
    
    def _extract_budget_hints(self, query: str) -> Optional[str]:
        """Extract sponsorship budget hints if mentioned."""
        import re
        
        # Look for budget ranges
        budget_patterns = [
            r'\$([\d,]+)\s*-\s*\$?([\d,]+)',
            r'budget\s+(?:of\s+)?\$?([\d,]+)',
            r'(?:under|below|max)\s+\$?([\d,]+)',
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return f"${match.group(1)}"
        
        # Look for qualitative budget signals
        if "premium" in query or "high-end" in query:
            return "high"
        elif "budget" in query or "affordable" in query:
            return "low"
        
        return None
    
    def _extract_exclusions(self, query: str) -> List[str]:
        """Extract keywords/events to exclude."""
        exclusions = []
        
        # Check for "not" or "except" phrases
        import re
        exclusion_patterns = [
            r'(?:not|except|excluding|avoid)\s+([^,]+)',
            r'no\s+([^,]+)',
        ]
        
        for pattern in exclusion_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            exclusions.extend([m.strip() for m in matches])
        
        return exclusions
    
    def _calculate_priorities(self, query: str, audience: Dict, 
                             objectives: List[str]) -> Dict[str, int]:
        """Calculate priority weights for different signals."""
        priorities = {
            "audience_quality": 30,
            "relevance": 25,
            "timing": 20,
            "location": 15,
            "cost_efficiency": 10
        }
        
        # Adjust based on objectives
        if "lead_generation" in objectives:
            priorities["audience_quality"] += 10
            priorities["relevance"] += 5
        
        if "brand_awareness" in objectives:
            priorities["relevance"] += 10
        
        if "cost_efficiency" in query or "budget" in query:
            priorities["cost_efficiency"] += 15
            priorities["audience_quality"] -= 5
        
        return priorities
    
    def _intent_to_dict(self, intent: UserIntent) -> Dict:
        """Convert UserIntent to dictionary for serialization."""
        return {
            "primary_goal": intent.primary_goal,
            "industry": intent.industry,
            "sub_industries": intent.sub_industries,
            "regions": intent.regions,
            "event_types": intent.event_types,
            "date_range": intent.date_range,
            "audience_target": intent.audience_target,
            "sponsorship_budget": intent.sponsorship_budget,
            "strategic_objectives": intent.strategic_objectives,
            "excluded_keywords": intent.excluded_keywords,
            "priority_signals": intent.priority_signals,
            "search_queries": intent.search_queries,
            "quality_requirements": intent.quality_requirements
        }
    
    def _extract_intent_with_llm(self, query: str, params: Dict) -> Optional[UserIntent]:
        """Extract intent using LLM for better accuracy."""
        try:
            from utils.llm_helpers import llm_call_with_json_output, INTENT_UNDERSTANDING_SYSTEM
            
            prompt = f"""
            Analyze this query for event sponsorship research and extract structured intent.
            
            Query: "{query}"
            Provided Industry: {params.get('industry', 'Not specified')}
            Provided Region: {params.get('region', 'Not specified')}
            
            Extract and return JSON with:
            - primary_goal: The main objective (lead_generation, brand_awareness, networking, etc.)
            - industry: Primary industry focus (fintech, healthcare, technology, etc.)
            - sub_industries: Array of related industries (max 3)
            - regions: Array of target locations (cities, countries, or regions)
            - event_types: Array of event types (conference, summit, expo, etc.)
            - date_range: Object with start_date and end_date (or null if not specified)
            - audience_target: Object describing target audience
            - sponsorship_budget: Budget hint if mentioned (or null)
            - strategic_objectives: Array of objectives
            - excluded_keywords: Array of things to exclude
            - search_queries: Array of 3-5 optimized search queries for finding events
            - priority_signals: Object with audience_quality, relevance, timing weights (0-100)
            
            Return only valid JSON.
            """
            
            result = llm_call_with_json_output(
                llm_func=self.llm,
                prompt=prompt,
                system_message=INTENT_UNDERSTANDING_SYSTEM,
                max_retries=2
            )
            
            if not result:
                return None
            
            # Build UserIntent from LLM result
            from datetime import datetime
            
            date_range = result.get('date_range', {})
            audience = result.get('audience_target', {})
            
            return UserIntent(
                primary_goal=result.get('primary_goal', 'lead_generation'),
                industry=result.get('industry', 'general'),
                sub_industries=result.get('sub_industries', [])[:3],
                regions=result.get('regions', []),
                event_types=result.get('event_types', ['conference']),
                date_range={
                    'start_date': date_range.get('start_date'),
                    'end_date': date_range.get('end_date'),
                    'flexibility': date_range.get('flexibility', '6 months')
                } if date_range else {'start_date': None, 'end_date': None, 'flexibility': '6 months'},
                audience_target={
                    'roles': audience.get('roles', []),
                    'company_types': audience.get('company_types', []),
                    'company_size': audience.get('company_size'),
                    'seniority': audience.get('seniority', [])
                } if audience else {'roles': [], 'company_types': [], 'seniority': []},
                sponsorship_budget=result.get('sponsorship_budget'),
                strategic_objectives=result.get('strategic_objectives', ['lead_generation']),
                excluded_keywords=result.get('excluded_keywords', []),
                priority_signals=result.get('priority_signals', {'audience_quality': 40, 'relevance': 40, 'timing': 20}),
                search_queries=result.get('search_queries', [f"{result.get('industry', 'general')} events 2025"]),
                quality_requirements={
                    'min_expected_attendance': None,
                    'preferred_formats': result.get('event_types', ['conference']),
                    'must_have': []
                }
            )
            
        except Exception as e:
            logger.warning(f"LLM intent extraction failed: {e}")
            return None
    
    def _calculate_confidence(self, intent: UserIntent) -> float:
        score = 0.7
        
        if intent.industry != "fintech":
            score += 0.1
        
        if len(intent.regions) > 0 and intent.regions[0] != "global":
            score += 0.1
        
        if len(intent.event_types) > 1:
            score += 0.05
        
        if len(intent.strategic_objectives) > 0:
            score += 0.05
        
        return min(score, 1.0)
