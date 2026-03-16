# Agents Registry

This file documents all agents in the marketing swarm. Each agent is responsible for a specific research task and passes results to the next agent in the pipeline.

## Input Parameters

The pipeline accepts these inputs:
- **Industry**: FinTech, Payments, Artificial Intelligence, Technology, etc.
- **Region**: USA, Europe, APAC, Middle East, Asia, global
- **Theme**: Specific topic (digital payments, blockchain, machine learning, etc.)

## Filtering Rules

The Event Discovery Agent applies strict filters:

| Rule | Description | Example |
|------|-------------|---------|
| **Exclude Vendor Events** | No company-specific product launches | Excludes: Google I/O, AWS re:Invent, Microsoft Build |
| **Industry-wide Only** | Public events with multiple participants | Includes: MAG Payments, MRC, Money20/20 |
| **Date Verification** | Verified dates only | Excludes events with uncertain dates |
| **Consistent Rules** | Same filter across all industries | Applied uniformly |

### Excluded Companies (Vendor Events)
Google, AWS, Amazon, Microsoft, Meta, Facebook, Apple, Salesforce, Oracle, IBM, Intel, Nvidia, Adobe, Shopify, Stripe, PayPal, Square, Zoom, Slack, GitHub, GitLab, Docker, Kubernetes, Twilio, Snowflake, Databricks, Cloudflare, HubSpot, Zendesk, Intercom, LinkedIn, Twitter, etc.

### Included Events (Industry-wide)
Conference, Summit, Expo, Forum, Festival, Convention, Symposium - that are open to the broader industry.

---

## JSON Schema

All agents share a common JSON schema for passing data:

```json
{
  "events": [
    {
      "event_name": "",
      "event_website": "",
      "city": "",
      "country": "",
      "expected_date": "",
      "theme": "",
      "organizer": "",
      "start_date": "",
      "end_date": "",
      "contact_email": "",
      "contact_url": "",
      "sponsorship_url": "",
      "summary": "",
      "industry_focus": "",
      "target_audience": "",
      "attendee_roles": "",
      "companies_attending": "",
      "technology_themes": "",
      "strategic_value": "",
      "potential_roi": "",
      "ideal_sponsorship_format": "",
      "audience_relevance_score": "",
      "industry_reputation_score": "",
      "attendance_score": "",
      "sponsor_value_score": "",
      "regional_importance_score": "",
      "overall_score": "",
      "priority_tier": "",
      "recommendation": "",
      "outreach_subject": "",
      "outreach_email": "",
      "date_verified": false,
      "status": "Discovered"
    }
  ]
}
```

---

## Agent Registry

| Agent Name | Description | Status |
|------------|--------------|--------|
| Event Discovery Agent | Discovers industry events with smart filtering | ✅ Active |
| Event Qualification Agent | Scores events for sponsorship potential | ✅ Active |
| Event Website Scraper Agent | Extracts event details from websites | ✅ Active |
| Event Intelligence Agent | Strategic analysis for sponsorship | ✅ Active |
| Event Prioritization Agent | Prioritizes and recommends events | ✅ Active |
| Outreach Email Agent | Generates sponsorship outreach emails | ✅ Active |
| Excel Table Generator Agent | Converts to Excel-ready format | ✅ Active |

---

## Agent Pipeline Flow

```
User Inputs: Industry + Region + Theme
    │
    ▼
┌─────────────────────────────────────┐
│   Event Discovery Agent             │ ← Applies vendor/event filters
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│   Event Qualification Agent         │ ← Scores & tiers events
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│   Event Website Scraper Agent       │ ← Extracts website details
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│   Event Intelligence Agent          │ ← Strategic analysis
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│   Event Prioritization Agent        │ ← Sorts & recommends
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│   Outreach Email Agent               │ ← Generates outreach
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│   Excel Table Generator Agent       │ ← Excel/CSV output
└─────────────────────────────────────┘
```

---

## Agent Details

### 1. Event Discovery Agent
- **Input**: Industry, Region, Theme (from CLI)
- **Filters Applied**:
  - Excludes company-specific events (Google, AWS, etc.)
  - Only includes industry-wide events
  - Verifies date accuracy
- **Output**: Event names, websites, locations, themes

### 2. Event Qualification Agent
- **Input**: Events from Discovery
- **Scores**: 1-10 for audience, reputation, attendance, sponsor value, regional importance
- **Output**: Overall score, priority tier (Tier 1-4)

### 3. Event Website Scraper Agent
- **Input**: Events with websites
- **Extracts**: Dates, contacts, sponsorship URL, about page info
- **Output**: Detailed event information

### 4. Event Intelligence Agent
- **Input**: Qualified events
- **Analysis**: Strategic value, ROI potential, sponsorship format
- **Output**: Attendee roles, companies, strategic value

### 5. Event Prioritization Agent
- **Input**: Analyzed events
- **Sorts**: By score and tier
- **Output**: Recommendation (Reach out immediately / Research further / Monitor)

### 6. Outreach Email Agent
- **Input**: Prioritized events
- **Generates**: Professional B2B sponsorship emails
- **Output**: Subject line, email body

### 7. Excel Table Generator Agent
- **Input**: All event data
- **Formats**: CSV, Markdown, Excel-ready
- **Output**: Structured table

---

## Usage Examples

```bash
# Payments industry, Middle East
python -m marketing_agents run --industry Payments --region "Middle East"

# AI conferences, APAC
python -m marketing_agents run --industry "Artificial Intelligence" --region APAC

# FinTech, global
python -m marketing_agents run --industry FinTech --region global

# With specific theme
python -m marketing_agents run --industry Payments --theme "digital payments" --region USA
```
