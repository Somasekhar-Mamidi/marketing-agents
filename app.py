"""Streamlit Web UI for Marketing Agents Pipeline - PRD Enhanced Version."""

import streamlit as st
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.orchestrator import Pipeline
from agents.schema_initialization import SchemaInitializationAgent
from agents.intent_understanding import IntentUnderstandingAgent
from agents.event_discovery import EventDiscoveryAgent
from agents.event_qualification import EventQualificationAgent
from agents.event_website_scraper import EventWebsiteScraperAgent
from agents.event_intelligence import EventIntelligenceAgent
from agents.event_prioritization import EventPrioritizationAgent
from agents.vendor_discovery import VendorDiscoveryAgent
from agents.outreach_email import OutreachEmailAgent
from agents.excel_table_generator import ExcelTableGeneratorAgent
from utils.search import WebSearchTool


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'findings': None,
        'selected_event': None,
        'pipeline_running': False,
        'run_count': 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def create_pipeline():
    """Create pipeline with all 10 agents."""
    pipeline = Pipeline()
    pipeline.add_agent(SchemaInitializationAgent())
    pipeline.add_agent(IntentUnderstandingAgent())
    pipeline.add_agent(EventDiscoveryAgent(max_events=30, provider="auto"))
    pipeline.add_agent(EventQualificationAgent())
    pipeline.add_agent(EventWebsiteScraperAgent())
    pipeline.add_agent(EventIntelligenceAgent())
    pipeline.add_agent(EventPrioritizationAgent())
    pipeline.add_agent(VendorDiscoveryAgent())
    pipeline.add_agent(OutreachEmailAgent())
    pipeline.add_agent(ExcelTableGeneratorAgent())
    return pipeline


def run_pipeline(industry: str, region: str, theme: str, time_range: str, max_events: int = 30):
    """Run the pipeline and return results."""
    pipeline = create_pipeline()
    
    query = f"{industry} events"
    if region:
        query += f" in {region}"
    
    params = {
        "industry": industry,
        "region": region,
        "theme": theme,
        "time_range": time_range,
        "max_events": max_events
    }
    
    result = pipeline.execute(query, initial_context={"parameters": params})
    return result.findings


def calculate_metrics(events):
    """Calculate dashboard metrics from events."""
    if not events:
        return {
            'total_events': 0,
            'tier1_count': 0,
            'tier2_count': 0,
            'avg_score': 0,
            'regions_covered': set()
        }
    
    tier1 = sum(1 for e in events if e.get('priority_tier', '').startswith('Tier 1'))
    tier2 = sum(1 for e in events if e.get('priority_tier', '').startswith('Tier 2'))
    
    scores = [float(e.get('overall_score', 0)) for e in events if e.get('overall_score')]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    regions = set()
    for e in events:
        if e.get('country'):
            regions.add(e.get('country'))
        if e.get('region'):
            regions.add(e.get('region'))
    
    return {
        'total_events': len(events),
        'tier1_count': tier1,
        'tier2_count': tier2,
        'avg_score': round(avg_score, 1),
        'regions_covered': regions
    }


def render_metrics_cards(metrics):
    """Render the metrics cards dashboard."""
    st.markdown("### 📊 Pipeline Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Events Discovered",
            value=metrics['total_events'],
            delta=None
        )
    
    with col2:
        st.metric(
            label="Tier 1 (Must Sponsor)",
            value=metrics['tier1_count'],
            delta="High Priority" if metrics['tier1_count'] > 0 else None,
            delta_color="normal" if metrics['tier1_count'] > 0 else "off"
        )
    
    with col3:
        st.metric(
            label="Tier 2 (Strong Opportunity)",
            value=metrics['tier2_count'],
            delta=None
        )
    
    with col4:
        st.metric(
            label="Avg Score",
            value=f"{metrics['avg_score']}/10",
            delta=None
        )


def render_sidebar():
    """Render sidebar with inputs."""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        industry = st.selectbox(
            "Industry",
            ["Payments", "FinTech", "Artificial Intelligence", "Technology", 
             "Software Development", "Open Source", "Blockchain", "E-commerce"],
            index=0
        )
        
        region = st.selectbox(
            "Region",
            ["", "USA", "Europe", "APAC", "Middle East", "Asia", "Latin America", 
             "North America", "South America", "Africa", "Global",
             "India", "Singapore", "Dubai", "Riyadh", "Brazil"],
            index=0
        )
        
        theme = st.text_input("Theme (optional)", placeholder="e.g., digital payments, machine learning")
        
        time_range = st.selectbox(
            "Time Range",
            ["12", "24"],
            format_func=lambda x: f"Next {x} months",
            index=0
        )
        
        max_events = st.slider(
            "Max Events to Discover",
            min_value=10,
            max_value=50,
            value=30,
            step=5,
            help="Number of events to search for"
        )
        
        st.divider()
        
        run_button = st.button("🚀 Run Pipeline", type="primary", use_container_width=True)
        
        st.divider()
        
        with st.expander("ℹ️ About"):
            st.markdown("""
            **Marketing Agents Pipeline**
            
            8 AI agents work sequentially to:
            1. Initialize schema
            2. Discover events
            3. Qualify opportunities
            4. Extract website data
            5. Analyze intelligence
            6. Prioritize targets
            7. Generate outreach emails
            8. Export to Excel
            """)
        
        return industry, region, theme, time_range, max_events, run_button


def render_event_table(events):
    """Render interactive event table with filtering and sorting."""
    st.markdown("### 📋 Event Results")
    
    if not events:
        st.warning("No events found.")
        return
    
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        tier_filter = st.multiselect(
            "Filter by Priority Tier",
            options=["Tier 1", "Tier 2", "Tier 3", "Tier 4"],
            default=["Tier 1", "Tier 2", "Tier 3", "Tier 4"]
        )
    
    with col_filter2:
        min_score = st.slider("Minimum Score", 0, 10, 0)
    
    filtered_events = [
        e for e in events 
        if (e.get('priority_tier', '') in tier_filter or not tier_filter)
        and (float(e.get('overall_score', 0)) >= min_score or not e.get('overall_score'))
    ]
    
    sort_col1, sort_col2 = st.columns(2)
    with sort_col1:
        sort_by = st.selectbox("Sort by", ["overall_score", "event_name", "country", "start_date"])
    with sort_col2:
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)
    
    reverse_sort = sort_order == "Descending"
    if sort_by == "overall_score":
        filtered_events = sorted(filtered_events, key=lambda x: float(x.get('overall_score', 0) or 0), reverse=reverse_sort)
    else:
        filtered_events = sorted(filtered_events, key=lambda x: x.get(sort_by, ''), reverse=reverse_sort)
    
    st.markdown(f"Showing **{len(filtered_events)}** of **{len(events)}** events")
    
    table_data = []
    for e in filtered_events:
        table_data.append({
            "Event Name": e.get('event_name', 'N/A'),
            "Location": f"{e.get('city', '')}, {e.get('country', '')}".strip(', '),
            "Date": e.get('start_date', e.get('expected_date', 'TBD')),
            "Theme": e.get('theme', 'N/A'),
            "Score": e.get('overall_score', 'N/A'),
            "Tier": e.get('priority_tier', 'N/A'),
        })
    
    if table_data:
        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    format="%.1f",
                    min_value=0,
                    max_value=10,
                ),
            }
        )


def render_event_detail_panel(event):
    """Render detailed event information in an expander."""
    with st.expander(f"📌 {event.get('event_name', 'Event Details')}", expanded=True):
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "🌐 Website", "🧠 Intelligence", "📧 Outreach"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Event Details")
                st.write(f"**Name:** {event.get('event_name', 'N/A')}")
                st.write(f"**Theme:** {event.get('theme', 'N/A')}")
                st.write(f"**Location:** {event.get('city', '')}, {event.get('country', '')}")
                st.write(f"**Organizer:** {event.get('organizer', 'N/A')}")
                st.write(f"**Status:** {event.get('status', 'N/A')}")
            
            with col2:
                st.markdown("#### Scores")
                st.write(f"**Overall Score:** {event.get('overall_score', 'N/A')}/10")
                st.write(f"**Priority Tier:** {event.get('priority_tier', 'N/A')}")
                st.write(f"**Recommendation:** {event.get('recommendation', 'N/A')}")
                st.write(f"**Audience Relevance:** {event.get('audience_relevance_score', 'N/A')}")
                st.write(f"**Industry Reputation:** {event.get('industry_reputation_score', 'N/A')}")
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Event Dates")
                st.write(f"**Expected:** {event.get('expected_date', 'N/A')}")
                st.write(f"**Start Date:** {event.get('start_date', 'N/A')}")
                st.write(f"**End Date:** {event.get('end_date', 'N/A')}")
            
            with col2:
                st.markdown("#### Contact Information")
                st.write(f"**Website:** [{event.get('event_website', '#')}]({event.get('event_website', '#')})")
                st.write(f"**Contact URL:** {event.get('contact_url', 'N/A')}")
                st.write(f"**Contact Email:** {event.get('contact_email', 'N/A')}")
                st.write(f"**Sponsorship URL:** {event.get('sponsorship_url', 'N/A')}")
            
            st.markdown("#### Summary")
            st.write(event.get('summary', 'No summary available.'))
            
            st.markdown("#### Target Audience")
            st.write(event.get('target_audience', 'N/A'))
            
            st.markdown("#### Industry Focus")
            st.write(event.get('industry_focus', 'N/A'))
        
        with tab3:
            st.markdown("#### Strategic Analysis")
            st.write(f"**Attendee Roles:** {event.get('attendee_roles', 'N/A')}")
            st.write(f"**Companies Attending:** {event.get('companies_attending', 'N/A')}")
            st.write(f"**Strategic Value:** {event.get('strategic_value', 'N/A')}")
            st.write(f"**Potential ROI:** {event.get('potential_roi', 'N/A')}")
            st.write(f"**Ideal Sponsorship Format:** {event.get('ideal_sponsorship_format', 'N/A')}")
        
        with tab4:
            render_email_panel(event)


def render_email_panel(event):
    """Render email panel with copy and action buttons."""
    st.markdown("#### Generated Outreach Email")
    
    subject = event.get('outreach_subject', '')
    body = event.get('outreach_email', '')
    
    if subject or body:
        email_text = f"Subject: {subject}\n\n{body}" if subject else body
        
        st.text_area("Email Content", value=email_text, height=200, key=f"email_{event.get('event_name', '')}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.button("📋 Copy Email", key=f"copy_{event.get('event_name', '')}")
        
        with col2:
            contact_email = event.get('contact_email', '')
            if contact_email and contact_email != 'N/A':
                mailto_link = f"mailto:{contact_email}?subject={subject}"
                st.markdown(f"[📧 Open Email Client]({mailto_link})")
            else:
                st.write("No contact email available")
        
        with col3:
            st.write("Ready to send")
    else:
        st.info("No outreach email generated yet.")


def render_export_section(findings):
    """Render export section with download buttons."""
    st.divider()
    st.markdown("### 📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if findings.get("csv"):
            st.download_button(
                label="📥 Download CSV",
                data=findings.get("csv", ""),
                file_name="events_export.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        st.download_button(
            label="📄 Download JSON",
            data=json.dumps(findings, indent=2),
            file_name="events_export.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        if findings.get("markdown"):
            st.download_button(
                label="📑 Download Markdown",
                data=findings.get("markdown", ""),
                file_name="events_export.md",
                mime="text/markdown",
                use_container_width=True
            )


def main():
    st.set_page_config(
        page_title="EventOps Intelligence Platform",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    st.title("🎯 EventOps Intelligence Platform")
    st.markdown("AI-powered event sponsorship research pipeline")
    
    industry, region, theme, time_range, max_events, run_button = render_sidebar()
    
    if run_button:
        if not industry:
            st.error("Please select an industry")
        else:
            st.session_state.pipeline_running = True
            st.session_state.run_count += 1
            
            with st.spinner("🔍 Running 8-agent pipeline... This may take a minute."):
                try:
                    findings = run_pipeline(industry, region, theme, time_range, max_events)
                    st.session_state.findings = findings
                    st.session_state.pipeline_running = False
                    
                    events = findings.get("events", [])
                    
                    st.success(f"✅ Pipeline complete! Found **{len(events)}** events")
                    
                    if events:
                        metrics = calculate_metrics(events)
                        render_metrics_cards(metrics)
                        
                        st.divider()
                        
                        render_event_table(events)
                        
                        st.divider()
                        
                        with st.expander("🔍 View Event Details", expanded=False):
                            for i, event in enumerate(events[:10]):
                                render_event_detail_panel(event)
                        
                        if len(events) > 10:
                            st.info(f"Showing details for first 10 events. Download JSON for full data.")
                        
                        render_export_section(findings)
                    else:
                        st.warning("No events found. Try different inputs.")
                        
                except Exception as e:
                    st.session_state.pipeline_running = False
                    st.error(f"Error: {str(e)}")
                    import traceback
                    with st.expander("View Error Details"):
                        st.code(traceback.format_exc())
    
    elif st.session_state.findings:
        events = st.session_state.findings.get("events", [])
        
        if events:
            metrics = calculate_metrics(events)
            render_metrics_cards(metrics)
            
            st.divider()
            render_event_table(events)
            
            st.divider()
            
            with st.expander("🔍 View Event Details"):
                for event in events[:10]:
                    render_event_detail_panel(event)
            
            render_export_section(st.session_state.findings)
    
    else:
        st.info("👈 Configure your search parameters in the sidebar and click 'Run Pipeline' to get started!")
        
        st.markdown("""
        ### How it works:
        
        | Step | Agent | Description |
        |------|-------|-------------|
        | 1 | Schema Init | Initialize empty event structure |
        | 2 | Event Discovery | Find industry events globally |
        | 3 | Qualification | Score events (1-10) and assign priority tiers |
        | 4 | Website Scraper | Extract event details from websites |
        | 5 | Intelligence | Strategic analysis and ROI potential |
        | 6 | Prioritization | Sort and recommend actions |
        | 7 | Outreach Emails | Generate professional sponsorship emails |
        | 8 | Excel Export | Download CSV, JSON, or Markdown |
        """)


if __name__ == "__main__":
    main()
