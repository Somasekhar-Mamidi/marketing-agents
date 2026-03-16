# Agents Registry

This file documents all agents in the marketing swarm. Each agent is responsible for a specific research task and passes results to the next agent in the pipeline.

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
      "status": "Researching"
    }
  ]
}
```

---

## Agent Registry

| Agent Name | Description | Status |
|------------|--------------|--------|
| Event Discovery Agent | Discovers industry events globally for sponsorship | ✅ Active |
| Event Qualification Agent | Scores events for sponsorship potential | ✅ Active |
| Event Website Scraper Agent | Extracts event details from websites | ✅ Active |
| Event Intelligence Agent | Strategic analysis for sponsorship | ✅ Active |
| Event Prioritization Agent | Prioritizes and recommends events | ✅ Active |
| Outreach Email Agent | Generates sponsorship outreach emails | ✅ Active |
| Excel Table Generator Agent | Converts to Excel-ready format | ✅ Active |

---

## Agent Pipeline Flow

```
User Prompt
    │
    ▼
┌─────────────────────────────────────┐
│   Event Discovery Agent             │ ← Finds events globally
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
- **Researches**: FinTech, Payments, AI, Technology, Software Development, Open Source events
- **Regions**: US, North America, South America, APAC, India, Singapore, Dubai, Riyadh, Middle East, Brazil
- **Output**: Event names, websites, locations, themes

### 2. Event Qualification Agent
- **Researches**: Event audience, reputation, attendance, sponsor value
- **Scores**: 1-10 for each category
- **Output**: Overall score, priority tier (Tier 1-4)

### 3. Event Website Scraper Agent
- **Researches**: Official event websites for dates, contacts, sponsorship info
- **Output**: Start/end dates, contact info, sponsorship URL

### 4. Event Intelligence Agent
- **Researches**: Strategic value, ROI, ideal sponsorship format
- **Output**: Attendee roles, companies, strategic value, ROI estimate

### 5. Event Prioritization Agent
- **Researches**: Strategic relevance, timing, brand exposure
- **Output**: Recommendation (Reach out immediately / Research further / Monitor)

### 6. Outreach Email Agent
- **Researches**: N/A (generates content based on event data)
- **Output**: Subject line, email body (professional B2B format)

### 7. Excel Table Generator Agent
- **Researches**: N/A (formats output)
- **Output**: CSV, Markdown table, Excel-ready format

---

## Pipeline Configuration

The pipeline is configured in `main.py`. All 7 agents run sequentially by default:

```python
pipeline.add_agent(EventDiscoveryAgent(max_events=50))
pipeline.add_agent(EventQualificationAgent())
pipeline.add_agent(EventWebsiteScraperAgent())
pipeline.add_agent(EventIntelligenceAgent())
pipeline.add_agent(EventPrioritizationAgent())
pipeline.add_agent(OutreachEmailAgent())
pipeline.add_agent(ExcelTableGeneratorAgent())
```
