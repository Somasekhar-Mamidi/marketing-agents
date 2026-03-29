def _is_vendor_only_search(query: str, industry: str) -> bool:
    query_lower = query.lower()
    vendor_keywords = ['vendor', 'vendors', 'booth', 'booths', 'contractor', 'contractors',
                       'service provider', 'service providers', 'exhibitor', 'exhibitors',
                       'sponsor', 'sponsors', 'builder', 'builders', 'stand builder']
    has_vendor_keyword = any(kw in query_lower for kw in vendor_keywords)
    event_keywords = ['event', 'events', 'conference', 'conferences', 'summit', 'summits',
                      'expo', 'expos', 'trade show', 'trade shows', 'forum', 'forums']
    has_event_keyword = any(kw in query_lower for kw in event_keywords)
    return has_vendor_keyword and not has_event_keyword
