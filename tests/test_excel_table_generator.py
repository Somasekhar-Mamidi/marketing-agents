"""Tests for Excel Table Generator Agent."""

import pytest
import json
from agents.excel_table_generator import ExcelTableGeneratorAgent
from agents.base import AgentInput


class TestExcelTableGeneratorAgent:
    """Test cases for ExcelTableGeneratorAgent."""
    
    def test_agent_initialization(self):
        """Test agent is properly initialized."""
        agent = ExcelTableGeneratorAgent()
        assert agent.name == "excel_table_generator"
        assert agent.description == "Converts events to Excel-ready table format"
    
    def test_execute_requires_events(self):
        """Test that execute requires events in context."""
        agent = ExcelTableGeneratorAgent()
        input_data = AgentInput(
            query="Generate Excel table",
            context={"events": []},
            parameters={}
        )
        
        result = agent.execute(input_data)
        assert result.status == "success"
    
    def test_execute_generates_csv(self, sample_event):
        """Test CSV generation."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert result.agent_name == "excel_table_generator"
        assert result.status == "success"
        assert "csv" in result.findings
        assert len(result.findings["csv"]) > 0
    
    def test_execute_generates_markdown(self, sample_event):
        """Test Markdown generation."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert "markdown" in result.findings
        assert len(result.findings["markdown"]) > 0
        assert "|" in result.findings["markdown"]
    
    def test_execute_generates_table(self, sample_event):
        """Test table array generation."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert "table" in result.findings
        assert len(result.findings["table"]) == 1
    
    def test_csv_has_headers(self, sample_event):
        """Test that CSV has proper headers."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        csv = result.findings["csv"]
        
        assert "Event Name" in csv
        assert "City" in csv
        assert "Country" in csv
    
    def test_csv_has_data_rows(self, sample_event):
        """Test that CSV has data rows."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        csv = result.findings["csv"]
        lines = csv.strip().split("\n")
        
        assert len(lines) >= 2
    
    def test_table_contains_key_columns(self, sample_event):
        """Test that table contains expected columns."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        table_row = result.findings["table"][0]
        
        expected_columns = [
            "Event Name", "City", "Country", "Expected Date",
            "Start Date", "End Date", "Theme", "Organizer",
            "Contact Email", "Overall Score", "Priority Tier",
            "Recommendation", "Status"
        ]
        
        for col in expected_columns:
            assert col in table_row
    
    def test_execute_handles_multiple_events(self, sample_events):
        """Test table generation for multiple events."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert len(result.findings["table"]) == 3
        assert result.findings["csv"] is not None
    
    def test_markdown_has_pipe_separators(self, sample_event):
        """Test that Markdown uses pipe separators."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        markdown = result.findings["markdown"]
        
        assert "|" in markdown
    
    def test_execute_preserves_event_data(self, sample_event):
        """Test that event data is preserved in output."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        table_row = result.findings["table"][0]
        
        assert table_row["Event Name"] == sample_event["event_name"]
        assert table_row["Overall Score"] == sample_event["overall_score"]
    
    def test_validate_input_requires_query(self):
        """Test that empty query raises error."""
        agent = ExcelTableGeneratorAgent()
        input_data = AgentInput(query="", context={}, parameters={})
        
        with pytest.raises(ValueError):
            agent.validate_input(input_data)
    
    def test_metadata_contains_event_count(self, sample_events):
        """Test that metadata contains event count."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": sample_events},
            parameters={}
        )
        
        result = agent.execute(input_data)
        
        assert "event_count" in result.metadata
        assert result.metadata["event_count"] == 3
    
    def test_csv_has_data(self, sample_event):
        """Test that CSV has data rows."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        csv = result.findings["csv"]
        
        assert "Test Payments Conference" in csv
    
    def test_markdown_includes_header_row(self, sample_event):
        """Test that Markdown includes header row."""
        agent = ExcelTableGeneratorAgent()
        
        input_data = AgentInput(
            query="Generate table",
            context={"events": [sample_event]},
            parameters={}
        )
        
        result = agent.execute(input_data)
        markdown = result.findings["markdown"]
        
        assert "Event Name" in markdown
        assert "Overall Score" in markdown
