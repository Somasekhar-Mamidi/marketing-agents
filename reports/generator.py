"""Markdown report generation for pipeline checkpoints."""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MarkdownReportGenerator:
    """Generates human-readable Markdown reports for review."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_event_report(
        self,
        events: List[Dict],
        pipeline_id: str,
        query: str,
        industry: str,
        region: str
    ) -> str:
        """Generate comprehensive event report.
        
        Returns:
            Path to generated report file
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        
        report = f"""# Event Research Report

**Pipeline ID:** {pipeline_id}  
**Generated:** {timestamp}  
**Query:** {query}  
**Industry:** {industry}  
**Region:** {region}

---

## Executive Summary

- **Total Events Discovered:** {len(events)}
- **Tier 1 Events:** {sum(1 for e in events if 'Tier 1' in e.get('priority_tier', ''))}
- **Tier 2 Events:** {sum(1 for e in events if 'Tier 2' in e.get('priority_tier', ''))}
- **Average Score:** {self._calculate_avg_score(events):.1f}/100

---

## Top Priority Events (Tier 1)

"""
        
        tier1_events = [e for e in events if 'Tier 1' in e.get('priority_tier', '')]
        tier1_events.sort(key=lambda x: float(x.get('overall_score', 0) or 0), reverse=True)
        
        for i, event in enumerate(tier1_events[:10], 1):
            report += self._format_event_detail(event, i)
        
        report += """
---

## Strong Opportunities (Tier 2)

"""
        
        tier2_events = [e for e in events if 'Tier 2' in e.get('priority_tier', '')]
        tier2_events.sort(key=lambda x: float(x.get('overall_score', 0) or 0), reverse=True)
        
        for i, event in enumerate(tier2_events[:10], 1):
            report += self._format_event_summary(event, i)
        
        report += """
---

## All Events Summary

| # | Event | Location | Date | Score | Tier | Action |
|---|-------|----------|------|-------|------|--------|
"""
        
        for i, event in enumerate(events, 1):
            report += self._format_event_table_row(event, i)
        
        report += """
---

## Regional Breakdown

"""
        report += self._generate_regional_breakdown(events)
        
        report += """
---

## Recommendations

"""
        report += self._generate_recommendations(events)
        
        # Save report
        filename = f"event_report_{pipeline_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        logger.info(f"Event report generated: {filepath}")
        return str(filepath)
    
    def generate_vendor_report(
        self,
        vendors: List[Dict],
        events: List[Dict],
        pipeline_id: str
    ) -> str:
        """Generate vendor research report."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        
        report = f"""# Vendor Research Report

**Pipeline ID:** {pipeline_id}  
**Generated:** {timestamp}

---

## Summary

- **Total Vendors Identified:** {len(vendors)}
- **Events Covered:** {len(events)}
- **Sponsors:** {sum(1 for v in vendors if v.get('vendor_type') == 'sponsor')}
- **Exhibitors:** {sum(1 for v in vendors if v.get('vendor_type') == 'exhibitor')}

---

## Top Vendors by Relevance

"""
        
        # Sort by relevance
        sorted_vendors = sorted(
            vendors,
            key=lambda x: x.get('relevance_score', 0),
            reverse=True
        )
        
        for i, vendor in enumerate(sorted_vendors[:20], 1):
            report += self._format_vendor_detail(vendor, i)
        
        report += """
---

## Vendors by Event

"""
        
        for event in events[:5]:  # Show for top 5 events
            event_vendors = [v for v in vendors if v.get('event_id') == event.get('id')]
            if event_vendors:
                report += f"### {event.get('event_name')}\n\n"
                for vendor in event_vendors[:5]:
                    report += f"- **{vendor.get('vendor_name')}** ({vendor.get('vendor_type')})\n"
                report += "\n"
        
        # Save report
        filename = f"vendor_report_{pipeline_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        logger.info(f"Vendor report generated: {filepath}")
        return str(filepath)
    
    def generate_email_report(
        self,
        emails: List[Dict],
        pipeline_id: str
    ) -> str:
        """Generate email draft report."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        
        report = f"""# Outreach Email Report

**Pipeline ID:** {pipeline_id}  
**Generated:** {timestamp}  
**Total Emails:** {len(emails)}

---

## Generated Emails

"""
        
        for i, email in enumerate(emails, 1):
            report += f"""### Email {i}: {email.get('recipient_name', 'Unknown')}

**To:** {email.get('recipient_email', 'N/A')}  
**Subject:** {email.get('subject', 'N/A')}

```
{email.get('body', '')}
```

**Status:** {email.get('status', 'draft')}

---

"""
        
        # Save report
        filename = f"email_report_{pipeline_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        logger.info(f"Email report generated: {filepath}")
        return str(filepath)
    
    def _format_event_detail(self, event: Dict, index: int) -> str:
        """Format detailed event section."""
        return f"""### {index}. {event.get('event_name')}

**Location:** {event.get('city', 'TBD')}, {event.get('country', 'TBD')}  
**Date:** {event.get('start_date', event.get('expected_date', 'TBD'))}  
**Website:** {event.get('event_website', 'N/A')}  
**Score:** {event.get('overall_score', 'N/A')}/100  
**Tier:** {event.get('priority_tier', 'N/A')}

**Summary:**  
{event.get('summary', 'No summary available.')}

**Target Audience:** {event.get('target_audience', 'N/A')}  
**Strategic Value:** {event.get('strategic_value', 'N/A')}

---

"""
    
    def _format_event_summary(self, event: Dict, index: int) -> str:
        """Format brief event summary."""
        return f"""### {index}. {event.get('event_name')}

- **Location:** {event.get('city', 'TBD')}, {event.get('country', 'TBD')}
- **Score:** {event.get('overall_score', 'N/A')}/100
- **Website:** {event.get('event_website', 'N/A')}

"""
    
    def _format_event_table_row(self, event: Dict, index: int) -> str:
        """Format event as table row."""
        location = f"{event.get('city', '')}, {event.get('country', '')}".strip(', ')
        date = event.get('start_date', event.get('expected_date', 'TBD'))
        score = event.get('overall_score', 'N/A')
        tier = event.get('priority_tier', '').split('-')[0].strip()
        action = event.get('recommendation', 'Review')
        
        return f"| {index} | {event.get('event_name', 'N/A')[:30]}... | {location[:20]} | {date} | {score} | {tier} | {action} |\n"
    
    def _format_vendor_detail(self, vendor: Dict, index: int) -> str:
        """Format vendor detail."""
        return f"""### {index}. {vendor.get('vendor_name')}

- **Type:** {vendor.get('vendor_type', 'Unknown')}
- **Relevance Score:** {vendor.get('relevance_score', 0)}/100
- **Event:** {vendor.get('event_name', 'N/A')}
- **Website:** {vendor.get('vendor_website', 'N/A')}
- **Contact:** {vendor.get('contact_email', 'N/A')}

"""
    
    def _calculate_avg_score(self, events: List[Dict]) -> float:
        """Calculate average event score."""
        scores = [float(e.get('overall_score', 0) or 0) for e in events if e.get('overall_score')]
        return sum(scores) / len(scores) if scores else 0
    
    def _generate_regional_breakdown(self, events: List[Dict]) -> str:
        """Generate regional breakdown section."""
        regions = {}
        for event in events:
            country = event.get('country', 'Unknown')
            if country not in regions:
                regions[country] = {'count': 0, 'avg_score': 0, 'events': []}
            regions[country]['count'] += 1
            score = float(event.get('overall_score', 0) or 0)
            regions[country]['events'].append(score)
        
        breakdown = "| Region | Events | Avg Score | Tier 1 | Tier 2 |\n"
        breakdown += "|--------|--------|-----------|--------|--------|\n"
        
        for country, data in sorted(regions.items(), key=lambda x: x[1]['count'], reverse=True):
            avg = sum(data['events']) / len(data['events']) if data['events'] else 0
            tier1 = sum(1 for e in events if e.get('country') == country and 'Tier 1' in e.get('priority_tier', ''))
            tier2 = sum(1 for e in events if e.get('country') == country and 'Tier 2' in e.get('priority_tier', ''))
            breakdown += f"| {country} | {data['count']} | {avg:.1f} | {tier1} | {tier2} |\n"
        
        return breakdown
    
    def _generate_recommendations(self, events: List[Dict]) -> str:
        """Generate recommendations section."""
        tier1 = [e for e in events if 'Tier 1' in e.get('priority_tier', '')]
        
        if tier1:
            recommendations = "### Immediate Action Required\n\n"
            recommendations += "The following Tier 1 events should be prioritized for sponsorship:\n\n"
            for event in tier1[:5]:
                recommendations += f"- **{event.get('event_name')}** - {event.get('recommendation', 'Contact immediately')}\n"
        else:
            recommendations = "### Suggestions\n\n"
            recommendations += "No Tier 1 events identified. Consider:\n"
            recommendations += "- Expanding search to additional regions\n"
            recommendations += "- Exploring adjacent industry events\n"
            recommendations += "- Reviewing Tier 2 opportunities\n"
        
        return recommendations


# Global generator instance
_generator: Optional[MarkdownReportGenerator] = None


def get_report_generator() -> MarkdownReportGenerator:
    """Get global report generator."""
    global _generator
    if _generator is None:
        _generator = MarkdownReportGenerator()
    return _generator
