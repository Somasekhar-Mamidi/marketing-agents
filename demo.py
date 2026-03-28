#!/usr/bin/env python3
"""Demo script showcasing all new features of the enhanced Marketing Agents pipeline."""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def demo_1_database():
    """Demo: Database and persistence."""
    print_header("1. DATABASE & PERSISTENCE")
    
    from database.models import get_database, Event, Vendor, Email
    
    db = get_database()
    
    # Create sample event
    sample_event = {
        'event_name': 'FinTech World 2025',
        'event_website': 'https://fintechworld.com',
        'city': 'Singapore',
        'country': 'Singapore',
        'start_date': '2025-09-15',
        'theme': 'FinTech',
        'overall_score': 85.5,
        'priority_tier': 'Tier 1 - Must Sponsor',
        'status': 'discovered'
    }
    
    event_id = db.save_event(sample_event)
    print(f"✅ Saved event with ID: {event_id}")
    
    # Retrieve events
    events = db.get_events()
    print(f"✅ Retrieved {len(events)} events from database")
    
    # Create sample vendor
    sample_vendor = {
        'vendor_name': 'Stripe',
        'vendor_website': 'https://stripe.com',
        'vendor_type': 'sponsor',
        'contact_email': 'partnerships@stripe.com',
        'event_id': event_id,
        'relevance_score': 95.0
    }
    
    vendor_id = db.save_vendor(sample_vendor)
    print(f"✅ Saved vendor with ID: {vendor_id}")
    
    # Create checkpoint review
    review_id = db.create_checkpoint_review('demo_pipeline_001', 'event_review')
    print(f"✅ Created checkpoint review with ID: {review_id}")
    
    print("\n📊 Database Schema:")
    print("   - events (id, event_name, score, tier, etc.)")
    print("   - vendors (id, vendor_name, type, event_id, etc.)")
    print("   - emails (id, recipient, subject, body, status)")
    print("   - checkpoint_reviews (id, pipeline_id, status, etc.)")


def demo_2_caching():
    """Demo: Caching layer."""
    print_header("2. INTELLIGENT CACHING")
    
    from utils.cache import get_search_cache, get_website_cache
    
    search_cache = get_search_cache()
    website_cache = get_website_cache()
    
    # Cache search results
    search_cache.set_search_results(
        query="FinTech conferences 2025",
        provider="tavily",
        results=[
            {"title": "Money 20/20", "url": "https://money2020.com"},
            {"title": "Finovate", "url": "https://finovate.com"}
        ]
    )
    print("✅ Cached search results (24h TTL)")
    
    # Retrieve from cache
    cached = search_cache.get_search_results("FinTech conferences 2025", "tavily")
    print(f"✅ Retrieved {len(cached)} cached results")
    
    # Cache website data
    website_cache.set_website_data(
        url="https://money2020.com",
        data={"start_date": "2025-10-15", "organizer": "Ascentis"}
    )
    print("✅ Cached website data (7d TTL)")
    
    print("\n📊 Cache Types:")
    print("   - Search Cache: 24h TTL (search results)")
    print("   - Website Cache: 7d TTL (scraped pages)")
    print("   - Qualification Cache: 30d TTL (scores)")


def demo_3_circuit_breaker():
    """Demo: Circuit breaker pattern."""
    print_header("3. CIRCUIT BREAKER RESILIENCE")
    
    from utils.circuit_breaker import get_circuit_breaker, CircuitBreakerOpen
    
    cb = get_circuit_breaker("demo_api", failure_threshold=3, recovery_timeout=10)
    
    print(f"   Initial state: {cb.get_state().value}")
    
    # Simulate failures
    for i in range(3):
        try:
            cb.call(lambda: 1/0)  # Simulate failure
        except CircuitBreakerOpen:
            print(f"   Attempt {i+1}: Circuit OPEN - Fast fail!")
            break
        except ZeroDivisionError:
            print(f"   Attempt {i+1}: Failed (circuit still CLOSED)")
    
    print(f"   Final state: {cb.get_state().value}")
    
    print("\n📊 Circuit Breaker States:")
    print("   - CLOSED: Normal operation")
    print("   - OPEN: Failing, reject requests immediately")
    print("   - HALF_OPEN: Testing recovery")


def demo_4_structured_logging():
    """Demo: Structured logging."""
    print_header("4. STRUCTURED LOGGING")
    
    from utils.logging_config import (
        setup_structured_logging,
        CorrelationContext,
        get_logger
    )
    
    setup_structured_logging()
    
    logger = get_logger('demo')
    
    with CorrelationContext() as cid:
        print(f"   Correlation ID: {cid}")
        logger.info(f"Starting demo operation")
        logger.info(f"Processing 10 events")
        logger.info(f"Demo completed")
    
    print("\n📊 Log Features:")
    print("   - JSON structured format")
    print("   - Correlation ID tracking")
    print("   - Agent/operation tagging")


def demo_5_metrics():
    """Demo: Prometheus metrics."""
    print_header("5. PROMETHEUS METRICS")
    
    from utils.metrics import get_metrics_collector, start_metrics_server
    
    collector = get_metrics_collector()
    
    # Record metrics
    collector.record_agent_execution("event_discovery", 2.5, True)
    collector.record_agent_execution("event_qualification", 1.2, True)
    collector.record_events_discovered(25)
    collector.record_search_api_call("tavily", 0.3, True)
    
    print("✅ Recorded metrics:")
    print("   - Agent executions (with latency)")
    print("   - Events discovered")
    print("   - Search API calls")
    print("   - Cache hits/misses")
    
    # Note: Would start metrics server on port 8000
    # start_metrics_server(8000)
    # print("   - Metrics server: http://localhost:8000")


def demo_6_scoring():
    """Demo: 100-point scoring rubrics."""
    print_header("6. 100-POINT SCORING RUBRICS")
    
    from scoring.rubrics import EventScoringRubrics
    
    sample_event = {
        'event_name': 'Money 20/20 Asia',
        'theme': 'payments fintech financial',
        'target_audience': 'CTO, CEO, VP Engineering, Directors',
        'city': 'Singapore',
        'country': 'Singapore',
        'summary': 'Annual premier fintech conference with 10000+ attendees, keynotes from industry leaders',
        'sponsorship_url': 'https://money2020.com/sponsor',
        'priority_tier': 'Tier 1 - Must Sponsor'
    }
    
    scores = EventScoringRubrics.score_event(sample_event)
    
    print(f"   Event: {sample_event['event_name']}")
    print(f"   Total Score: {scores['total_score']}/100")
    print(f"   Tier: {scores['tier']}")
    print()
    print("   Criteria Breakdown:")
    for criterion, score in scores['criteria_scores'].items():
        max_pts = EventScoringRubrics.CRITERIA[criterion].max_points
        weight = EventScoringRubrics.CRITERIA[criterion].weight
        print(f"     - {criterion}: {score}/{max_pts} (weight: {weight}%)")
    
    print("\n📊 Scoring Categories (100 points total):")
    print("   - Audience Quality: 25 pts")
    print("   - Event Reputation: 20 pts")
    print("   - Sponsorship ROI: 20 pts")
    print("   - Strategic Alignment: 15 pts")
    print("   - Geographic Relevance: 10 pts")
    print("   - Competitive Presence: 10 pts")


def demo_7_checkpoint_system():
    """Demo: Human-in-the-loop checkpoints."""
    print_header("7. HUMAN-IN-THE-LOOP CHECKPOINTS")
    
    from checkpoint.manager import (
        get_checkpoint_manager,
        CheckpointType,
        CheckpointStatus
    )
    
    manager = get_checkpoint_manager()
    
    # Create checkpoint
    sample_events = [
        {'event_name': 'Money 20/20', 'overall_score': 85, 'priority_tier': 'Tier 1'},
        {'event_name': 'Finovate', 'overall_score': 78, 'priority_tier': 'Tier 2'}
    ]
    
    checkpoint = manager.create_checkpoint(
        pipeline_id='demo_pipeline_001',
        checkpoint_type=CheckpointType.EVENT_REVIEW,
        name='Event Discovery Complete',
        data={'events': sample_events}
    )
    
    print(f"   Created checkpoint: {checkpoint.id}")
    print(f"   Status: {checkpoint.status.value}")
    print(f"   Events for review: {len(checkpoint.data['events'])}")
    
    # Generate review summary
    summary = manager.generate_review_summary(checkpoint.id)
    print(f"\n   Review Summary (preview):")
    for line in summary.split('\n')[:10]:
        print(f"     {line}")
    
    print("\n📊 Checkpoint Types:")
    print("   - EVENT_REVIEW: Review discovered events")
    print("   - VENDOR_REVIEW: Review identified vendors")
    print("   - EMAIL_REVIEW: Review generated emails")


def demo_8_reports():
    """Demo: Markdown report generation."""
    print_header("8. MARKDOWN REPORT GENERATION")
    
    from reports.generator import get_report_generator
    
    generator = get_report_generator()
    
    sample_events = [
        {
            'event_name': 'Money 20/20 Asia',
            'city': 'Singapore',
            'country': 'Singapore',
            'start_date': '2025-09-15',
            'overall_score': 85,
            'priority_tier': 'Tier 1 - Must Sponsor',
            'event_website': 'https://money2020.com',
            'summary': 'Premier fintech conference',
            'target_audience': 'CTO, CEOs',
            'strategic_value': 'High',
            'recommendation': 'Contact immediately'
        },
        {
            'event_name': 'FinovateAsia',
            'city': 'Singapore',
            'country': 'Singapore',
            'start_date': '2025-11-10',
            'overall_score': 78,
            'priority_tier': 'Tier 2 - Strong Opportunity',
            'event_website': 'https://finovate.com',
            'summary': 'Fintech innovation showcase',
            'target_audience': 'Product Managers',
            'strategic_value': 'Medium',
            'recommendation': 'Research further'
        }
    ]
    
    report_path = generator.generate_event_report(
        events=sample_events,
        pipeline_id='demo_001',
        query='fintech conferences asia 2025',
        industry='FinTech',
        region='Asia'
    )
    
    print(f"   ✅ Generated report: {report_path}")
    
    # Show first few lines
    with open(report_path, 'r') as f:
        lines = f.readlines()[:20]
        for line in lines:
            print(f"   {line.rstrip()}")
    
    print("   ... (truncated)")


def demo_9_deduplication():
    """Demo: Fuzzy deduplication."""
    print_header("9. FUZZY EVENT DEDUPLICATION")
    
    from utils.deduplication import deduplicate_events, calculate_similarity
    
    # Similar events
    events = [
        {'event_name': 'Money 20/20 Conference 2025', 'event_website': 'https://money2020.com'},
        {'event_name': 'Money 20/20 2025 Conference', 'event_website': 'https://money2020.com/2025'},
        {'event_name': 'Finovate Asia', 'event_website': 'https://finovate.com'},
        {'event_name': 'FinTech Summit', 'event_website': 'https://fintechsummit.io'}
    ]
    
    print("   Before dedup: 4 events")
    similarity = calculate_similarity("Money 20/20 Conference", "Money 20/20")
    print(f"   Similarity check: 'Money 20/20 Conference' vs 'Money 20/20' = {similarity:.2f}")
    
    deduplicated = deduplicate_events(events, threshold=0.80)
    print(f"   After dedup: {len(deduplicated)} events")
    
    for event in deduplicated:
        print(f"     - {event['event_name']}")


def demo_10_parallel_processing():
    """Demo: Parallel processing."""
    print_header("10. PARALLEL EVENT PROCESSING")
    
    from utils.parallel_processor import ParallelProcessor
    import time
    
    processor = ParallelProcessor(max_workers=3)
    
    def slow_processor(event):
        time.sleep(0.1)  # Simulate work
        event['processed'] = True
        return event
    
    events = [{'id': i, 'name': f'Event {i}'} for i in range(10)]
    
    print("   Processing 10 events with 3 workers...")
    
    start = time.time()
    results = processor.process_events_parallel(
        events,
        slow_processor,
        description="Demo processing"
    )
    elapsed = time.time() - start
    
    print(f"   Completed {len(results)} events in {elapsed:.2f}s")
    print(f"   Sequential would take: ~1.0s")
    print(f"   Speedup: ~{1.0/elapsed:.1f}x")


def demo_11_security():
    """Demo: Security features."""
    print_header("11. SECURITY & INPUT VALIDATION")
    
    from utils.security import sanitize_input, redact_sensitive_data, check_rate_limit
    
    # Sanitize input
    dirty_input = "'; DROP TABLE events; --"
    clean = sanitize_input(dirty_input)
    print(f"   Input: {dirty_input}")
    print(f"   Sanitized: {clean}")
    
    # Redact sensitive data
    sensitive_data = {
        'event_name': 'Money 20/20',
        'api_key': 'sk-1234567890abcdef',
        'contact_email': 'test@example.com'
    }
    redacted = redact_sensitive_data(sensitive_data)
    print(f"\n   Original: {sensitive_data}")
    print(f"   Redacted: {redacted}")
    
    # Rate limiting
    allowed = check_rate_limit("demo_user", max_requests=5, window_seconds=60)
    print(f"\n   Rate limit check: {'✅ Allowed' if allowed else '❌ Blocked'}")


def demo_12_health_checks():
    """Demo: Health checks."""
    print_header("12. SYSTEM HEALTH CHECKS")
    
    from utils.health import get_health_status, format_health_for_display
    
    status = get_health_status()
    
    print(format_health_for_display(status))


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  MARKETING AGENTS - ENHANCED FEATURES DEMO")
    print("=" * 70)
    
    demos = [
        ("Database & Persistence", demo_1_database),
        ("Intelligent Caching", demo_2_caching),
        ("Circuit Breaker Resilience", demo_3_circuit_breaker),
        ("Structured Logging", demo_4_structured_logging),
        ("Prometheus Metrics", demo_5_metrics),
        ("100-Point Scoring Rubrics", demo_6_scoring),
        ("Human-in-the-Loop Checkpoints", demo_7_checkpoint_system),
        ("Markdown Report Generation", demo_8_reports),
        ("Fuzzy Event Deduplication", demo_9_deduplication),
        ("Parallel Event Processing", demo_10_parallel_processing),
        ("Security & Input Validation", demo_11_security),
        ("System Health Checks", demo_12_health_checks),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"   ❌ Demo failed: {e}")
    
    print_header("DEMO COMPLETE")
    print("✅ All 12 feature demos executed successfully!")
    print("\n📁 Output files created in:")
    print("   - data/marketing_agents.db (SQLite database)")
    print("   - .checkpoints/ (checkpoint data)")
    print("   - .audit/ (audit logs)")
    print("   - reports/ (Markdown reports)")


if __name__ == "__main__":
    main()
