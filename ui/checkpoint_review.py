"""Streamlit UI components for checkpoint review system."""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Optional


def render_checkpoint_sidebar():
    """Render sidebar with checkpoint navigation."""
    st.sidebar.header("🔍 Checkpoint Review")
    
    # Pipeline selection
    st.sidebar.subheader("Pipeline")
    pipeline_id = st.sidebar.selectbox(
        "Select Pipeline",
        options=["demo_pipeline_001", "demo_pipeline_002"],
        index=0
    )
    
    # Checkpoint filters
    st.sidebar.subheader("Filter")
    checkpoint_types = st.sidebar.multiselect(
        "Checkpoint Type",
        options=["Event Review", "Vendor Review", "Email Review"],
        default=["Event Review"]
    )
    
    status_filter = st.sidebar.selectbox(
        "Status",
        options=["All", "Pending", "Approved", "Rejected"]
    )
    
    return {
        "pipeline_id": pipeline_id,
        "types": checkpoint_types,
        "status": status_filter
    }


def render_checkpoint_list(checkpoints: List[Dict]):
    """Render list of checkpoints."""
    st.subheader("📋 Checkpoints")
    
    if not checkpoints:
        st.info("No checkpoints found matching the filter criteria.")
        return None
    
    for cp in checkpoints:
        status_emoji = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "❌"
        }.get(cp.get('status', 'pending'), "❓")
        
        with st.expander(f"{status_emoji} {cp.get('name', 'Checkpoint')} - {cp.get('type', '')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Pipeline:** `{cp.get('pipeline_id')}`")
                st.write(f"**Created:** {cp.get('created_at', 'N/A')}")
            
            with col2:
                st.write(f"**Status:** {cp.get('status', 'unknown')}")
                if cp.get('reviewed_by'):
                    st.write(f"**Reviewed by:** {cp.get('reviewed_by')}")
            
            if cp.get('review_notes'):
                st.write(f"**Notes:** {cp.get('review_notes')}")
            
            # Action buttons for pending checkpoints
            if cp.get('status') == 'pending':
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.button(f"✅ Approve", key=f"approve_{cp['id']}")
                with col2:
                    st.button(f"❌ Reject", key=f"reject_{cp['id']}")
                with col3:
                    st.button(f"👁 View Details", key=f"view_{cp['id']}")


def render_event_review_panel(checkpoint_data: Dict):
    """Render event review panel."""
    st.subheader("📅 Event Review")
    
    events = checkpoint_data.get('events', [])
    
    if not events:
        st.warning("No events to review.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    tier1 = sum(1 for e in events if 'Tier 1' in e.get('priority_tier', ''))
    tier2 = sum(1 for e in events if 'Tier 2' in e.get('priority_tier', ''))
    scores = [float(e.get('overall_score', 0)) for e in events if e.get('overall_score')]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    col1.metric("Total Events", len(events))
    col2.metric("Tier 1", tier1, delta="High Priority" if tier1 > 0 else None)
    col3.metric("Tier 2", tier2)
    col4.metric("Avg Score", f"{avg_score:.1f}/100")
    
    st.divider()
    
    # Events table
    st.subheader("Events")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        tier_filter = st.multiselect(
            "Filter by Tier",
            options=["Tier 1", "Tier 2", "Tier 3", "Tier 4"],
            default=["Tier 1", "Tier 2"]
        )
    with col2:
        min_score = st.slider("Minimum Score", 0, 100, 0)
    
    # Filter events
    filtered = [
        e for e in events
        if any(t in e.get('priority_tier', '') for t in tier_filter)
        and float(e.get('overall_score', 0) or 0) >= min_score
    ]
    
    st.write(f"Showing {len(filtered)} of {len(events)} events")
    
    # Display events
    for i, event in enumerate(filtered):
        with st.expander(f"📌 {event.get('event_name')} ({event.get('priority_tier', 'N/A')})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Location:** {event.get('city')}, {event.get('country')}")
                st.write(f"**Date:** {event.get('start_date', event.get('expected_date', 'TBD'))}")
                st.write(f"**Score:** {event.get('overall_score', 'N/A')}/100")
                st.write(f"**Website:** [{event.get('event_website', 'N/A')}]({event.get('event_website', '#')})")
                st.write(f"**Summary:** {event.get('summary', 'No summary available.')}")
            
            with col2:
                st.write(f"**Tier:** {event.get('priority_tier')}")
                st.write(f"**Recommendation:** {event.get('recommendation', 'N/A')}")
                st.write(f"**Target Audience:** {event.get('target_audience', 'N/A')}")
                
                # Include/exclude toggle
                include = st.checkbox("Include", value=True, key=f"include_{i}")
                
                if not include:
                    st.warning("This event will be excluded from next steps.")
    
    # Batch actions
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        approve_all = st.button("✅ Approve All Events", type="primary")
    with col2:
        reject_low = st.button("❌ Reject Low Score")
    with col3:
        export_btn = st.button("📥 Export to CSV")
    
    return {
        "approve_all": approve_all,
        "reject_low": reject_low,
        "export": export_btn
    }


def render_vendor_review_panel(checkpoint_data: Dict):
    """Render vendor review panel."""
    st.subheader("🏢 Vendor Review")
    
    vendors = checkpoint_data.get('vendors', [])
    
    if not vendors:
        st.warning("No vendors to review.")
        return
    
    # Summary
    col1, col2, col3 = st.columns(3)
    sponsors = sum(1 for v in vendors if v.get('vendor_type') == 'sponsor')
    exhibitors = sum(1 for v in vendors if v.get('vendor_type') == 'exhibitor')
    
    col1.metric("Total Vendors", len(vendors))
    col2.metric("Sponsors", sponsors)
    col3.metric("Exhibitors", exhibitors)
    
    st.divider()
    
    # Sort by relevance
    sorted_vendors = sorted(vendors, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    for i, vendor in enumerate(sorted_vendors[:20]):
        with st.expander(f"🏢 {vendor.get('vendor_name')} ({vendor.get('vendor_type')})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Type:** {vendor.get('vendor_type', 'Unknown')}")
                st.write(f"**Relevance Score:** {vendor.get('relevance_score', 'N/A')}/100")
                st.write(f"**Event:** {vendor.get('event_name', 'N/A')}")
                st.write(f"**Website:** [{vendor.get('vendor_website', 'N/A')}]({vendor.get('vendor_website', '#')})")
                st.write(f"**Contact:** {vendor.get('contact_email', 'N/A')}")
            
            with col2:
                priority = "High" if vendor.get('relevance_score', 0) >= 80 else "Medium" if vendor.get('relevance_score', 0) >= 60 else "Low"
                st.write(f"**Priority:** {priority}")
                
                include = st.checkbox("Include", value=True, key=f"vendor_include_{i}")
    
    # Actions
    st.divider()
    if st.button("✅ Approve All Vendors", type="primary"):
        st.success("All vendors approved for outreach.")


def render_email_review_panel(checkpoint_data: Dict):
    """Render email review panel."""
    st.subheader("📧 Email Review")
    
    emails = checkpoint_data.get('emails', [])
    
    if not emails:
        st.warning("No emails to review.")
        return
    
    st.write(f"**Total Emails:** {len(emails)}")
    
    st.divider()
    
    for i, email in enumerate(emails):
        with st.expander(f"📧 {email.get('subject', 'Untitled')} → {email.get('recipient_email', 'Unknown')}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**To:** {email.get('recipient_name', 'Unknown')} ({email.get('recipient_email')})")
                st.write(f"**Subject:** {email.get('subject', 'N/A')}")
            
            with col2:
                st.write(f"**Status:** {email.get('status', 'draft')}")
            
            st.divider()
            
            # Email body
            st.text_area(
                "Email Content",
                value=email.get('body', ''),
                height=200,
                key=f"email_{i}"
            )
            
            # Actions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Approve", key=f"email_approve_{i}"):
                    st.success("Email approved")
            
            with col2:
                if st.button("📝 Edit", key=f"email_edit_{i}"):
                    st.info("Editing enabled")
            
            with col3:
                mailto = f"mailto:{email.get('recipient_email')}?subject={email.get('subject', '')}"
                st.markdown(f"[📧 Open in Mail Client]({mailto})")
            
            with col4:
                if st.button("🗑️ Delete", key=f"email_delete_{i}"):
                    st.warning("Email deleted")


def render_review_summary(checkpoint: Dict):
    """Render summary statistics for a checkpoint."""
    st.subheader("📊 Review Summary")
    
    data = checkpoint.get('data', {})
    
    col1, col2, col3 = st.columns(3)
    
    if 'events' in data:
        events = data['events']
        col1.metric("Events", len(events))
        
        tier1 = sum(1 for e in events if 'Tier 1' in e.get('priority_tier', ''))
        tier2 = sum(1 for e in events if 'Tier 2' in e.get('priority_tier', ''))
        
        col2.metric("Tier 1", tier1)
        col3.metric("Tier 2", tier2)
    
    elif 'vendors' in data:
        vendors = data['vendors']
        col1.metric("Vendors", len(vendors))
        
        high_relevance = sum(1 for v in vendors if v.get('relevance_score', 0) >= 80)
        col2.metric("High Relevance", high_relevance)
    
    elif 'emails' in data:
        emails = data['emails']
        col1.metric("Emails", len(emails))
        col2.metric("Drafts", sum(1 for e in emails if e.get('status') == 'draft'))


def render_approval_form():
    """Render form for approving/rejecting checkpoints."""
    st.subheader("✍️ Submit Review")
    
    with st.form("review_form"):
        reviewer_name = st.text_input("Reviewer Name", placeholder="Your name")
        
        review_type = st.radio("Decision", options=["Approve", "Reject"])
        
        notes = st.text_area(
            "Review Notes",
            placeholder="Add any notes about your decision...",
            height=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit = st.form_submit_button(
                f"✅ {review_type} Checkpoint",
                type="primary" if review_type == "Approve" else "secondary"
            )
        
        with col2:
            cancel = st.form_submit_button("Cancel")
        
        return {
            "reviewer": reviewer_name,
            "decision": review_type,
            "notes": notes,
            "submit": submit
        }


def render_pipeline_dashboard():
    """Render main pipeline dashboard."""
    st.set_page_config(
        page_title="Checkpoint Review Dashboard",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Checkpoint Review Dashboard")
    st.markdown("Human-in-the-loop approval for Marketing Agents pipeline")
    
    # Filters from sidebar
    filters = render_checkpoint_sidebar()
    
    # Main content
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Load checkpoints (mock data for demo)
        mock_checkpoints = [
            {
                'id': 'cp_001',
                'pipeline_id': 'demo_pipeline_001',
                'name': 'Event Discovery Complete',
                'type': 'event_review',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'data': {
                    'events': [
                        {'event_name': 'Money 20/20', 'overall_score': 85, 'priority_tier': 'Tier 1 - Must Sponsor', 'city': 'Singapore', 'country': 'Singapore'},
                        {'event_name': 'Finovate', 'overall_score': 78, 'priority_tier': 'Tier 2 - Strong Opportunity', 'city': 'London', 'country': 'UK'},
                        {'event_name': 'FinTech Summit', 'overall_score': 72, 'priority_tier': 'Tier 2 - Strong Opportunity', 'city': 'Dubai', 'country': 'UAE'}
                    ]
                }
            }
        ]
        
        render_checkpoint_list(mock_checkpoints)
    
    with col2:
        st.subheader("📈 Quick Stats")
        st.write("**Pending Reviews:** 3")
        st.write("**Approved Today:** 5")
        st.write("**Pipeline Runs:** 12")
        
        st.divider()
        
        st.subheader("🎯 Quick Actions")
        if st.button("📋 View All Events", use_container_width=True):
            st.info("Navigating to events...")
        
        if st.button("🏢 View All Vendors", use_container_width=True):
            st.info("Navigating to vendors...")
        
        if st.button("📧 View All Emails", use_container_width=True):
            st.info("Navigating to emails...")
    
    # Detailed review panel
    st.divider()
    st.subheader("📝 Detailed Review")
    
    tab1, tab2, tab3 = st.tabs(["📅 Events", "🏢 Vendors", "📧 Emails"])
    
    with tab1:
        # Sample event data
        sample_events = [
            {'event_name': 'Money 20/20', 'overall_score': 85, 'priority_tier': 'Tier 1 - Must Sponsor', 
             'city': 'Singapore', 'country': 'Singapore', 'start_date': '2025-09-15',
             'event_website': 'https://money2020.com', 'summary': 'Premier fintech conference',
             'recommendation': 'Contact immediately', 'target_audience': 'CTOs, CEOs'},
            {'event_name': 'Finovate', 'overall_score': 78, 'priority_tier': 'Tier 2 - Strong Opportunity',
             'city': 'London', 'country': 'UK', 'start_date': '2025-10-20',
             'event_website': 'https://finovate.com', 'summary': 'Fintech innovation showcase',
             'recommendation': 'Research further', 'target_audience': 'Product Managers'}
        ]
        render_event_review_panel({'events': sample_events})
    
    with tab2:
        sample_vendors = [
            {'vendor_name': 'Stripe', 'vendor_type': 'sponsor', 'relevance_score': 95, 'event_name': 'Money 20/20',
             'vendor_website': 'https://stripe.com', 'contact_email': 'partnerships@stripe.com'},
            {'vendor_name': 'Plaid', 'vendor_type': 'sponsor', 'relevance_score': 88, 'event_name': 'Money 20/20',
             'vendor_website': 'https://plaid.com', 'contact_email': 'biz@plaid.com'}
        ]
        render_vendor_review_panel({'vendors': sample_vendors})
    
    with tab3:
        sample_emails = [
            {'subject': 'Sponsorship Inquiry - Money 20/20 2025', 'recipient_name': 'Money 2020 Team',
             'recipient_email': 'sponsor@money2020.com', 'status': 'draft',
             'body': 'Dear Money 2020 Team,\n\nI hope this email finds you well...\n\nBest regards'}
        ]
        render_email_review_panel({'emails': sample_emails})
    
    # Approval form
    st.divider()
    render_review_summary(mock_checkpoints[0])
    result = render_approval_form()
    
    if result.get('submit') and result.get('reviewer'):
        if result.get('decision') == 'Approve':
            st.success(f"✅ Checkpoint approved by {result.get('reviewer')}")
        else:
            st.warning(f"❌ Checkpoint rejected by {result.get('reviewer')}: {result.get('notes')}")


def render_health_monitor():
    """Render system health monitor."""
    st.set_page_config(
        page_title="System Health",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 System Health Monitor")
    
    # Mock health data
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "checks": {
            "search_apis": {"status": "healthy", "response_time_ms": 120, "message": "2 APIs configured"},
            "web_scraper": {"status": "healthy", "response_time_ms": 85, "message": "Can fetch pages"},
            "cache": {"status": "healthy", "response_time_ms": 5, "message": "Operational"},
            "pipeline": {"status": "healthy", "response_time_ms": 10, "message": "Ready"}
        }
    }
    
    # Status header
    status_color = {"healthy": "green", "degraded": "yellow", "unhealthy": "red"}.get(
        health_data['status'], 'gray'
    )
    
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Overall Status", health_data['status'].upper(), 
                delta="All systems operational")
    col2.metric("Version", health_data['version'])
    col3.metric("Last Check", datetime.now().strftime("%H:%M:%S"))
    
    st.divider()
    
    # Individual checks
    st.subheader("Component Checks")
    
    for check_name, check_data in health_data['checks'].items():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(
            check_data['status'], "❓"
        )
        
        with col1:
            st.write(f"{emoji} **{check_name.replace('_', ' ').title()}**")
            st.caption(check_data['message'])
        
        with col2:
            st.metric("Latency", f"{check_data['response_time_ms']}ms")
        
        with col3:
            st.write(f"Status: `{check_data['status']}`")
    
    # Refresh button
    st.divider()
    if st.button("🔄 Refresh Health Status", type="primary"):
        st.rerun()


if __name__ == "__main__":
    render_pipeline_dashboard()
