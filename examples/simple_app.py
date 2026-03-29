#!/usr/bin/env python3
"""
Simplified Marketing Agents App - Uses ONLY DuckDuckGo (no API keys needed)

Run with: streamlit run simple_app.py
"""

import streamlit as st
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import json

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Event Discovery (DuckDuckGo Only)",
    page_icon="🦆",
    layout="wide",
    initial_sidebar_state="expanded"
)


def discover_events_duckduckgo(industry: str, region: str = "", max_results: int = 20) -> List[Dict]:
    """Discover events using only DuckDuckGo (no APIs)."""
    from utils.duckduckgo_search import SimpleDuckDuckGoSearch
    
    searcher = SimpleDuckDuckGoSearch()
    
    with st.spinner("🔍 Searching DuckDuckGo for events..."):
        raw_results = searcher.search_events(
            industry=industry,
            region=region,
            year="2025",
            max_results=max_results
        )
    
    # Parse results into event format
    events = []
    for result in raw_results:
        event = {
            "event_name": result.get("title", "Unknown Event").split("|")[0].strip(),
            "event_website": result.get("url", ""),
            "summary": result.get("content", ""),
            "theme": industry,
            "city": "",
            "country": region if region else "",
            "expected_date": "",
            "overall_score": "0",
            "priority_tier": "Tier 3 - Optional",
            "status": "Discovered",
            "source": "duckduckgo"
        }
        events.append(event)
    
    return events


def simple_score_event(event: Dict) -> Dict:
    """Simple rule-based scoring (no LLM needed)."""
    name = event.get("event_name", "").lower()
    summary = event.get("summary", "").lower()
    
    score = 50  # Base score
    
    # Boost for high-value keywords
    high_value = ["summit", "conference", "world", "global", "premier"]
    for kw in high_value:
        if kw in name:
            score += 10
    
    # Boost for 2025 dates
    if "2025" in name or "2025" in summary:
        score += 10
    
    # Cap at 100
    score = min(score, 100)
    
    # Determine tier
    if score >= 80:
        tier = "Tier 1 - Must Sponsor"
    elif score >= 60:
        tier = "Tier 2 - Strong Opportunity"
    elif score >= 40:
        tier = "Tier 3 - Optional"
    else:
        tier = "Tier 4 - Low Priority"
    
    event["overall_score"] = str(score)
    event["priority_tier"] = tier
    
    return event


def generate_simple_email(event: Dict) -> Dict:
    """Generate simple outreach email."""
    event_name = event.get("event_name", "the event")
    
    subject = f"Sponsorship Inquiry - {event_name}"
    
    body = f"""Dear {event_name} Team,

I hope this email finds you well.

I am reaching out from [Your Company] regarding sponsorship opportunities for {event_name}.

We are interested in learning more about:
- Available sponsorship tiers and benefits
- Branding and visibility opportunities  
- Expected attendee demographics

Could we schedule a brief call to discuss potential partnership opportunities?

Looking forward to hearing from you.

Best regards,
[Your Name]
[Your Company]
[Your Phone]
"""
    
    return {
        "event_name": event_name,
        "subject": subject,
        "body": body
    }


def render_header():
    """Render app header."""
    st.title("🦆 Event Discovery Platform")
    st.markdown("**Powered by DuckDuckGo** - No API keys required!")
    st.divider()


def render_sidebar():
    """Render sidebar with controls."""
    with st.sidebar:
        st.header("🔍 Search Configuration")
        
        industry = st.selectbox(
            "Industry",
            ["FinTech", "Payments", "AI", "Technology", "SaaS", "Cybersecurity"],
            index=0
        )
        
        region = st.selectbox(
            "Region (optional)",
            ["", "USA", "Europe", "Asia", "Singapore", "Dubai", "London"],
            index=0
        )
        
        max_events = st.slider(
            "Max Events",
            min_value=5,
            max_value=50,
            value=20
        )
        
        st.divider()
        
        st.markdown("**Features:**")
        st.markdown("✅ Free DuckDuckGo search")
        st.markdown("✅ No API keys needed")
        st.markdown("✅ Rule-based scoring")
        st.markdown("✅ Email generation")
        st.markdown("✅ CSV export")
        
        return industry, region, max_events


def render_search_results(events: List[Dict]):
    """Render discovered events."""
    st.subheader(f"📅 Discovered {len(events)} Events")
    
    if not events:
        st.warning("No events found. Try different search terms.")
        return
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    tier1 = sum(1 for e in events if "Tier 1" in e.get("priority_tier", ""))
    tier2 = sum(1 for e in events if "Tier 2" in e.get("priority_tier", ""))
    avg_score = sum(int(e.get("overall_score", 0)) for e in events) / len(events) if events else 0
    
    col1.metric("Total Events", len(events))
    col2.metric("Tier 1", tier1)
    col3.metric("Tier 2", tier2)
    col4.metric("Avg Score", f"{avg_score:.0f}/100")
    
    st.divider()
    
    # Events table
    table_data = []
    for e in events:
        table_data.append({
            "Event": e.get("event_name", "")[:50] + "..." if len(e.get("event_name", "")) > 50 else e.get("event_name", ""),
            "Score": e.get("overall_score", "0"),
            "Tier": e.get("priority_tier", "").split("-")[0].strip(),
            "Website": e.get("event_website", "")[:30] + "..." if len(e.get("event_website", "")) > 30 else e.get("event_website", "")
        })
    
    if table_data:
        st.dataframe(table_data, use_container_width=True)
    
    # Individual event details
    st.subheader("Event Details")
    
    for i, event in enumerate(events):
        with st.expander(f"📌 {event.get('event_name', 'Unknown')}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Website:** [{event.get('event_website', 'N/A')}]({event.get('event_website', '#')})")
                st.write(f"**Score:** {event.get('overall_score')}/100")
                st.write(f"**Tier:** {event.get('priority_tier')}")
                st.write(f"**Summary:** {event.get('summary', 'N/A')}")
            
            with col2:
                if st.button("📧 Generate Email", key=f"email_{i}"):
                    email = generate_simple_email(event)
                    st.session_state[f"email_{i}"] = email
                    st.success("Email generated!")
                
                # Show email if generated
                if f"email_{i}" in st.session_state:
                    email = st.session_state[f"email_{i}"]
                    st.text_area("Subject", email["subject"], key=f"subj_{i}")
                    st.text_area("Body", email["body"], height=150, key=f"body_{i}")
    
    # Export
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV export
        import pandas as pd
        df = pd.DataFrame(events)
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # JSON export
        json_str = json.dumps(events, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_str,
            file_name=f"events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


def main():
    """Main app function."""
    render_header()
    
    industry, region, max_events = render_sidebar()
    
    # Search button
    col1, col2 = st.columns([1, 4])
    with col1:
        search_clicked = st.button("🔍 Search Events", type="primary", use_container_width=True)
    with col2:
        st.write("Click to search DuckDuckGo for industry events")
    
    # Perform search
    if search_clicked:
        try:
            events = discover_events_duckduckgo(industry, region, max_events)
            
            # Score events
            for event in events:
                simple_score_event(event)
            
            # Store in session
            st.session_state.events = events
            st.session_state.search_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            st.error(f"Search failed: {e}")
            logger.error(f"Search error: {e}", exc_info=True)
    
    # Display results
    if "events" in st.session_state:
        events = st.session_state.events
        
        st.success(f"✅ Found {len(events)} events (searched at {st.session_state.get('search_time', 'N/A')})")
        render_search_results(events)
    else:
        # Welcome message
        st.info("👈 Configure your search and click 'Search Events' to start!")
        
        st.markdown("### How it works:")
        st.markdown("1. Select your **Industry** (FinTech, Payments, AI, etc.)")
        st.markdown("2. Optionally select a **Region** for targeted results")
        st.markdown("3. Set the **Max Events** to discover")
        st.markdown("4. Click **Search Events** to find conferences using DuckDuckGo")
        st.markdown("5. Review scored events and generate outreach emails")
        st.markdown("6. Export results to **CSV** or **JSON**")
        
        st.divider()
        
        st.markdown("### Sample Events You'll Discover:")
        sample_events = [
            {"name": "Money 20/20", "location": "Singapore", "type": "FinTech"},
            {"name": "Finovate", "location": "London", "type": "FinTech"},
            {"name": "Web Summit", "location": "Lisbon", "type": "Technology"},
            {"name": "AI Summit", "location": "New York", "type": "AI"},
        ]
        
        for event in sample_events:
            st.markdown(f"- **{event['name']}** ({event['type']}) - {event['location']}")


if __name__ == "__main__":
    main()
