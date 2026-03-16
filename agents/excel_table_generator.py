"""Excel Table Generator Agent - Converts events to Excel-ready table format."""

import json
import logging
from typing import List, Dict, Any
from agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class ExcelTableGeneratorAgent(BaseAgent):
    """Converts event data to Excel/Google Sheets ready format.
    
    Outputs a structured table with columns:
    - Event Name, City, Country, Expected Date, Start Date, End Date
    - Theme, Organizer, Contact Email, Contact URL, Sponsorship URL
    - Overall Score, Priority Tier, Recommendation
    - Outreach Subject, Outreach Email, Status
    """
    
    name = "excel_table_generator"
    description = "Converts events to Excel-ready table format"
    
    # Column headers for Excel output
    COLUMNS = [
        "Event Name",
        "City",
        "Country",
        "Expected Date",
        "Start Date",
        "End Date",
        "Theme",
        "Organizer",
        "Contact Email",
        "Contact URL",
        "Sponsorship URL",
        "Overall Score",
        "Priority Tier",
        "Recommendation",
        "Outreach Subject",
        "Outreach Email",
        "Status"
    ]
    
    # Map schema fields to columns
    FIELD_MAP = {
        "Event Name": "event_name",
        "City": "city",
        "Country": "country",
        "Expected Date": "expected_date",
        "Start Date": "start_date",
        "End Date": "end_date",
        "Theme": "theme",
        "Organizer": "organizer",
        "Contact Email": "contact_email",
        "Contact URL": "contact_url",
        "Sponsorship URL": "sponsorship_url",
        "Overall Score": "overall_score",
        "Priority Tier": "priority_tier",
        "Recommendation": "recommendation",
        "Outreach Subject": "outreach_subject",
        "Outreach Email": "outreach_email",
        "Status": "status"
    }
    
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Generate Excel table from events."""
        self.validate_input(input_data)
        
        # Get events from context
        events = input_data.context.get("events", [])
        
        if not events:
            return AgentOutput(
                agent_name=self.name,
                findings={
                    "events": [],
                    "table": "No events to display",
                    "csv": ""
                },
                metadata={"agent": self.name, "event_count": 0}
            )
        
        logger.info(f"Generating Excel table for {len(events)} events")
        
        # Generate table data
        table_data = self._generate_table(events)
        
        # Generate CSV
        csv_content = self._generate_csv(events)
        
        # Generate markdown table
        markdown_table = self._generate_markdown(events)
        
        return AgentOutput(
            agent_name=self.name,
            findings={
                "events": events,
                "table": table_data,
                "csv": csv_content,
                "markdown": markdown_table
            },
            metadata={
                "agent": self.name, 
                "event_count": len(events),
                "columns": len(self.COLUMNS)
            }
        )
    
    def _generate_table(self, events: List[Dict]) -> List[Dict]:
        """Generate table-ready data."""
        table_data = []
        
        for event in events:
            row = {}
            for col_name, field_name in self.FIELD_MAP.items():
                value = event.get(field_name, "")
                row[col_name] = value if value else "N/A"
            table_data.append(row)
        
        return table_data
    
    def _generate_csv(self, events: List[Dict]) -> str:
        """Generate CSV content."""
        # Header row
        csv_lines = [",".join(self.COLUMNS)]
        
        # Data rows
        for event in events:
            row_values = []
            for col_name, field_name in self.FIELD_MAP.items():
                value = event.get(field_name, "")
                # Escape quotes and wrap in quotes if contains comma
                value = str(value).replace('"', '""')
                if "," in value or '"' in value or "\n" in value:
                    value = f'"{value}"'
                row_values.append(value)
            csv_lines.append(",".join(row_values))
        
        return "\n".join(csv_lines)
    
    def _generate_markdown(self, events: List[Dict]) -> str:
        """Generate Markdown table."""
        # Header row
        markdown = "| " + " | ".join(self.COLUMNS) + " |\n"
        
        # Separator row
        markdown += "| " + " | ".join(["---" for _ in self.COLUMNS]) + " |\n"
        
        # Data rows
        for event in events:
            row_values = []
            for col_name, field_name in self.FIELD_MAP.items():
                value = event.get(field_name, "")
                # Truncate long values
                value = str(value)[:50] if len(str(value)) > 50 else str(value)
                # Escape pipe characters
                value = value.replace("|", "\\|")
                row_values.append(value if value else "N/A")
            markdown += "| " + " | ".join(row_values) + " |\n"
        
        return markdown
    
    def _format_for_excel(self, value: Any) -> str:
        """Format value for Excel display."""
        if value is None:
            return ""
        return str(value)
