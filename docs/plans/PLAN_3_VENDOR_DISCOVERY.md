# DEEP PLAN 3: Vendor Discovery & Booth Builder Module

## Executive Summary
Build a comprehensive vendor discovery system that automatically finds booth builders, exhibition contractors, and event service providers for any event location, with integrated email outreach capabilities.

## Timeline: 2 weeks

---

## Phase 1: Enhanced Vendor Agent (Days 1-4)

### 1.1 Service Provider Categories
Define comprehensive vendor taxonomy:

```python
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
    'photography': {
        'keywords': ['event photography', 'videography', 
                     'live streaming', 'event coverage'],
        'search_queries': [
            '{location} event photography services',
            '{location} corporate event videography',
        ]
    },
    'staffing': {
        'keywords': ['event staffing', 'hostess agency', 
                     'promotional staff', 'interpreters'],
        'search_queries': [
            '{location} event staffing agency',
            '{location} exhibition hostess services',
        ]
    }
}
```

### 1.2 Enhanced VendorDiscoveryAgent

#### Core Capabilities
- [ ] Direct location-based search (no event required)
- [ ] Event-linked vendor discovery
- [ ] Multi-category parallel search
- [ ] Intelligent result ranking

#### Search Strategies
1. **Web Search Integration**
   - Tavily API for comprehensive results
   - Serper for Google results
   - DuckDuckGo fallback

2. **Directory Scraping**
   - ExpoStandZone integration
   - Industry-specific directories
   - Chamber of commerce listings

3. **LinkedIn/Social Discovery** (Future)
   - Company pages
   - Recent projects

### 1.3 Vendor Data Model

```python
@dataclass
class Vendor:
    id: str
    name: str
    category: str  # booth_builder, av_equipment, etc.
    location: Location
    
    # Contact
    website: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    contact_page_url: Optional[str]
    
    # Details
    description: str
    services: List[str]
    years_in_business: Optional[int]
    
    # Portfolio
    portfolio_url: Optional[str]
    case_studies: List[CaseStudy]
    
    # Ratings & Reviews
    rating: Optional[float]  # 0-5
    review_count: Optional[int]
    
    # Linked data
    event_id: Optional[str]  # If discovered for specific event
    distance_from_venue_km: Optional[float]
    
    # Metadata
    source: str  # 'search', 'directory', 'manual'
    discovered_at: datetime
    last_verified: Optional[datetime]

@dataclass
class CaseStudy:
    title: str
    event_name: Optional[str]
    location: Optional[str]
    booth_size: Optional[str]
    images: List[str]
    description: str
```

### 1.4 Search Result Parser

#### Website Scraping
- [ ] Extract company name from title/meta
- [ ] Find contact information (email, phone)
- [ ] Locate contact/portfolio pages
- [ ] Extract description/about text
- [ ] Find service offerings

#### Contact Discovery
- [ ] Search "contact us" page
- [ ] Look for email patterns on site
- [ ] Extract phone numbers
- [ ] Find LinkedIn/social links

**Deliverable:** Enhanced vendor agent that can find any service provider by location

---

## Phase 2: Booth Builder Search (Days 5-8)

### 2.1 Location-Aware Search

#### Venue Distance Calculation
```python
from geopy.distance import geodesic

def calculate_vendor_distance(
    vendor_location: str, 
    venue_address: str
) -> float:
    """Calculate km distance between vendor and venue."""
    # Use geocoding API (Google Maps, OpenStreetMap)
    vendor_coords = geocode(vendor_location)
    venue_coords = geocode(venue_address)
    
    return geodesic(vendor_coords, venue_coords).kilometers
```

#### Search Query Builder
```python
def build_booth_builder_queries(
    venue_city: str,
    venue_country: str,
    event_name: Optional[str] = None
) -> List[str]:
    queries = [
        f"exhibition stand builders {venue_city}",
        f"booth contractors {venue_city} {venue_country}",
        f"custom booth design {venue_city}",
        f"trade show booth rental {venue_city}",
    ]
    
    if event_name:
        queries.extend([
            f"{event_name} booth builders",
            f"{event_name} official contractors",
        ])
    
    return queries
```

### 2.2 ATPS Dublin Specific Implementation

For your specific use case - ATPS Dublin booth builders:

```python
# Direct search for ATPS Dublin
atps_search = VendorDiscoveryAgent()
vendors = atps_search.search_service_providers(
    category='booth_builder',
    location='Dublin, Ireland',
    venue_address='Crowne Plaza Dublin Airport, Northwood Park, Santry Demesne, Dublin',
    max_results=10
)

# Expected vendors to find:
# - Buttonbox Exhibition (Portlaoise, ~80km)
# - Vinehall Displays (The Ward, ~15km) ⭐ Closest
# - ECS (Kildare, ~50km)
# - 53 Degrees Design (Dublin)
```

### 2.3 Vendor Scoring & Ranking

#### Scoring Criteria
```python
VENDOR_SCORE_WEIGHTS = {
    'distance_from_venue': 0.30,  # Closer is better
    'years_experience': 0.20,     # More is better
    'portfolio_quality': 0.20,    # Case studies, images
    'response_time': 0.15,        # Historical (if known)
    'rating_reviews': 0.15,       # 0-5 star rating
}

def score_vendor(vendor: Vendor, venue_location: str) -> float:
    score = 0
    
    # Distance score (inverse - closer is higher)
    if vendor.distance_from_venue_km:
        distance_score = max(0, 100 - vendor.distance_from_venue_km) / 100
        score += distance_score * VENDOR_SCORE_WEIGHTS['distance_from_venue']
    
    # Experience score
    if vendor.years_in_business:
        exp_score = min(vendor.years_in_business / 20, 1.0)  # Cap at 20 years
        score += exp_score * VENDOR_SCORE_WEIGHTS['years_experience']
    
    # Portfolio score
    portfolio_score = len(vendor.case_studies) / 10  # Normalize
    score += min(portfolio_score, 1.0) * VENDOR_SCORE_WEIGHTS['portfolio_quality']
    
    # Rating score
    if vendor.rating:
        rating_score = vendor.rating / 5.0
        score += rating_score * VENDOR_SCORE_WEIGHTS['rating_reviews']
    
    return score * 10  # 0-10 scale
```

### 2.4 Portfolio Extraction

#### Automated Portfolio Discovery
- [ ] Find "Work", "Portfolio", "Projects", "Case Studies" pages
- [ ] Extract images and descriptions
- [ ] Use vision AI to categorize booth types (custom vs modular)
- [ ] Identify booth sizes from descriptions

#### Manual Portfolio Addition
- [ ] UI for uploading portfolio images
- [ ] Link to specific events
- [ ] Tag with booth specifications

**Deliverable:** Intelligent booth builder search with distance-based ranking

---

## Phase 3: Email Automation (Days 9-11)

### 3.1 Email Template System

#### Template Variables
```typescript
interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  variables: string[];
}

// Variables available:
// {{vendor_name}} - Company name
// {{event_name}} - Event name
// {{event_dates}} - Event dates
// {{venue_name}} - Venue name
// {{venue_location}} - Venue address
// {{booth_size}} - Booth dimensions (user-filled)
// {{company_name}} - Juspay
// {{sender_name}} - Your name
// {{sender_title}} - Your title
// {{sender_phone}} - Your phone
// {{sender_email}} - Your email
```

#### Pre-built Templates

**Template 1: Initial Booth Inquiry**
```
Subject: Booth Setup Inquiry - {{event_name}} ({{event_dates}})

Hi {{vendor_name}} Team,

I hope this message finds you well.

My name is {{sender_name}} from {{company_name}}, and we are sponsoring 
{{event_name}} taking place on {{event_dates}} at {{venue_name}} in 
{{venue_location}}.

We would like to discuss booth setup requirements for our exhibition space 
and would appreciate your expertise in creating an impactful presence at 
this event.

Event Details:
- Event: {{event_name}}
- Date: {{event_dates}}
- Venue: {{venue_name}}
- Location: {{venue_location}}
- Booth Size: [TO BE FILLED - e.g., 10x10 ft, 20x20 ft]

Our Requirements:
- Custom booth design and build
- Graphics and branding installation
- Delivery, setup, and dismantle services
- [ADD ANY OTHER SPECIFIC REQUIREMENTS]

Next Steps:
Could we schedule a 20-30 minute call this week or next to discuss:
1. Design concepts and portfolio examples
2. Timeline and delivery schedule
3. Pricing and package options
4. Any additional services (furniture, AV, storage)

Please let me know your availability, or feel free to share your calendar link.

Looking forward to hearing from you.

Best regards,

{{sender_name}}
{{sender_title}}
{{company_name}}
{{sender_phone}}
{{sender_email}}
```

### 3.2 Email Composition UI

#### Rich Text Editor (Optional)
- [ ] Integrate TipTap or Slate.js
- [ ] Variable insertion dropdown
- [ ] Preview mode with real data
- [ ] Template selection

#### Simple Editor (MVP)
- [ ] Textarea with variable highlighting
- [ ] Variable selector buttons
- [ ] Live preview panel
- [ ] Subject line editor

### 3.3 Bulk Email Features

#### Multi-Select Vendors
- [ ] Checkbox selection in vendor list
- [ ] "Select All" option
- [ ] Bulk actions toolbar

#### Personalization at Scale
- [ ] Mail merge functionality
- [ ] Per-vendor customization
- [ ] Send rate limiting (avoid spam)

#### Email Tracking (Future)
- [ ] Open tracking
- [ ] Click tracking
- [ ] Reply detection

**Deliverable:** Email system with templates and bulk sending

---

## Phase 4: Vendor Management UI (Days 12-14)

### 4.1 Vendor List Page

#### Layout
```
┌──────────────────────────────────────────────────────┐
│  Vendors & Outreach                    [✉️ Compose]  │
├──────────────────────────────────────────────────────┤
│  [🔍 Search]  [🏷 Category ▼]  [📍 Distance ▼]       │
├──────────────────────────────────────────────────────┤
│  [All] [Booth Builders] [AV] [Catering] [Printing]  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ☑️  🏗️ Buttonbox Exhibition    📍 80km from venue  │
│      Dublin, Ireland              ⭐ 4.9/5          │
│      📧 info@buttonbox.ie                          │
│      [✉️ Email] [🔗 Portfolio] [📞 Call]           │
│                                                      │
│  ☑️  🎨 Vinehall Displays       📍 15km from venue │
│      Dublin, Ireland              ⭐ 4.8/5          │
│      📧 info@vinehall.ie                           │
│      [✉️ Email] [🔗 Portfolio] [📞 Call]           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 4.2 Vendor Detail Modal

#### Sections
1. **Overview**
   - Company info
   - Contact details
   - Services offered

2. **Portfolio**
   - Image gallery
   - Case studies
   - Past events worked

3. **Communication History**
   - Emails sent
   - Responses received
   - Call notes

4. **Quote/Proposal**
   - Upload vendor quotes
   - Compare pricing
   - Notes and decisions

### 4.3 Comparison Tool

#### Side-by-Side Vendor Comparison
```
┌──────────────┬──────────────┬──────────────┐
│  Buttonbox   │  Vinehall    │  ECS         │
├──────────────┼──────────────┼──────────────┤
│ ⭐ 4.9       │ ⭐ 4.8       │ ⭐ 4.7       │
│ 📍 80km      │ 📍 15km ⭐   │ 📍 50km      │
│ 💰 $15k      │ 💰 $18k      │ 💰 $14k      │
│ 🏗️ Custom   │ 🏗️ Custom   │ 🏗️ Modular  │
└──────────────┴──────────────┴──────────────┘
```

### 4.4 Integration with Events

#### Event-Vendor Linking
- [ ] Show vendors for specific event
- [ ] Mark vendor as "contacted"
- [ ] Track vendor response
- [ ] Set vendor status (interested, quoted, selected, rejected)

**Deliverable:** Complete vendor management interface

---

## API Endpoints

### Vendor Discovery
```
POST /api/vendors/search
{
  "category": "booth_builder",
  "location": "Dublin, Ireland",
  "venue_address": "Crowne Plaza Dublin Airport...",
  "max_results": 10
}

Response: {
  "vendors": [
    {
      "id": "vendor_123",
      "name": "Vinehall Displays",
      "distance_km": 15,
      "rating": 4.8,
      "email": "info@vinehall.ie",
      "phone": "+353 1 835 9674",
      "website": "https://vinehall.ie",
      "portfolio_url": "https://vinehall.ie/case-studies/"
    }
  ]
}
```

### Email Sending
```
POST /api/vendors/email
{
  "vendor_ids": ["vendor_123", "vendor_456"],
  "template_id": "booth_inquiry",
  "variables": {
    "event_name": "ATPS Dublin 2025",
    "booth_size": "10x10 ft",
    "sender_name": "Somasekhar Mamidi"
  },
  "custom_message": "Additional note..."
}
```

---

## Success Metrics
- [ ] Find 10+ booth builders for any major city in < 30 seconds
- [ ] Distance calculation accurate to ±5km
- [ ] Email templates customizable with 10+ variables
- [ ] Vendor comparison supports 3+ vendors side-by-side
- [ ] Portfolio images load < 2 seconds
- [ ] Email send rate: 10 emails/minute (rate limited)

---

## Estimated Effort
- **Total:** 14 days (2 weeks)
- **Backend:** 7 days
- **Frontend:** 5 days
- **Testing:** 2 days
