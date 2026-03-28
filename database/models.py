"""Database models for persistent storage."""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event database model."""
    id: Optional[int]
    event_name: str
    event_website: str
    city: Optional[str]
    country: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    theme: str
    organizer: Optional[str]
    overall_score: float
    priority_tier: str
    status: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


@dataclass
class Vendor:
    """Vendor database model."""
    id: Optional[int]
    vendor_name: str
    vendor_website: Optional[str]
    vendor_type: str  # sponsor, exhibitor, partner
    contact_email: Optional[str]
    contact_phone: Optional[str]
    linkedin_url: Optional[str]
    relevance_score: float
    event_id: Optional[int]
    status: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


@dataclass
class Email:
    """Email database model."""
    id: Optional[int]
    recipient_type: str  # 'event' or 'vendor'
    recipient_id: int
    subject: str
    body: str
    status: str  # 'draft', 'sent', 'scheduled'
    gmail_draft_id: Optional[str]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class Database:
    """SQLite database for persistent storage."""
    
    def __init__(self, db_path: str = "data/marketing_agents.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT NOT NULL,
                    event_website TEXT NOT NULL,
                    city TEXT,
                    country TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    theme TEXT NOT NULL,
                    organizer TEXT,
                    overall_score REAL DEFAULT 0,
                    priority_tier TEXT DEFAULT 'Tier 4 - Low Priority',
                    status TEXT DEFAULT 'discovered',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Vendors table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vendors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor_name TEXT NOT NULL,
                    vendor_website TEXT,
                    vendor_type TEXT DEFAULT 'sponsor',
                    contact_email TEXT,
                    contact_phone TEXT,
                    linkedin_url TEXT,
                    relevance_score REAL DEFAULT 0,
                    event_id INTEGER,
                    status TEXT DEFAULT 'identified',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (event_id) REFERENCES events (id)
                )
            """)
            
            # Emails table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient_type TEXT NOT NULL,
                    recipient_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    gmail_draft_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Pipeline runs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline_id TEXT NOT NULL UNIQUE,
                    query TEXT NOT NULL,
                    industry TEXT,
                    region TEXT,
                    status TEXT DEFAULT 'running',
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    events_count INTEGER DEFAULT 0,
                    vendors_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Checkpoint reviews table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoint_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline_id TEXT NOT NULL,
                    checkpoint_name TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    reviewer_notes TEXT,
                    approved_at TEXT,
                    approved_by TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def save_event(self, event: Dict) -> int:
        """Save or update an event."""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.utcnow().isoformat()
            
            # Check if event exists by website
            cursor = conn.execute(
                "SELECT id FROM events WHERE event_website = ?",
                (event.get('event_website'),)
            )
            existing = cursor.fetchone()
            
            metadata = {k: v for k, v in event.items() 
                       if k not in ['id', 'event_name', 'event_website', 'city', 
                                   'country', 'start_date', 'end_date', 'theme',
                                   'organizer', 'overall_score', 'priority_tier', 'status']}
            
            if existing:
                # Update
                conn.execute("""
                    UPDATE events SET
                        event_name = ?,
                        city = ?,
                        country = ?,
                        start_date = ?,
                        end_date = ?,
                        theme = ?,
                        organizer = ?,
                        overall_score = ?,
                        priority_tier = ?,
                        status = ?,
                        updated_at = ?,
                        metadata = ?
                    WHERE id = ?
                """, (
                    event.get('event_name'),
                    event.get('city'),
                    event.get('country'),
                    event.get('start_date'),
                    event.get('end_date'),
                    event.get('theme'),
                    event.get('organizer'),
                    float(event.get('overall_score', 0) or 0),
                    event.get('priority_tier', 'Tier 4 - Low Priority'),
                    event.get('status', 'discovered'),
                    now,
                    json.dumps(metadata),
                    existing[0]
                ))
                return existing[0]
            else:
                # Insert
                cursor = conn.execute("""
                    INSERT INTO events
                    (event_name, event_website, city, country, start_date, end_date,
                     theme, organizer, overall_score, priority_tier, status,
                     created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.get('event_name'),
                    event.get('event_website'),
                    event.get('city'),
                    event.get('country'),
                    event.get('start_date'),
                    event.get('end_date'),
                    event.get('theme'),
                    event.get('organizer'),
                    float(event.get('overall_score', 0) or 0),
                    event.get('priority_tier', 'Tier 4 - Low Priority'),
                    event.get('status', 'discovered'),
                    now, now,
                    json.dumps(metadata)
                ))
                return cursor.lastrowid
    
    def get_events(self, status: Optional[str] = None, tier: Optional[str] = None) -> List[Dict]:
        """Get events with optional filtering."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if tier:
                query += " AND priority_tier = ?"
                params.append(tier)
            
            query += " ORDER BY overall_score DESC"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                event = dict(row)
                event['metadata'] = json.loads(event.get('metadata', '{}'))
                events.append(event)
            
            return events
    
    def save_vendor(self, vendor: Dict) -> int:
        """Save or update a vendor."""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.utcnow().isoformat()
            
            metadata = {k: v for k, v in vendor.items()
                       if k not in ['id', 'vendor_name', 'vendor_website', 'vendor_type',
                                   'contact_email', 'contact_phone', 'linkedin_url',
                                   'relevance_score', 'event_id', 'status']}
            
            cursor = conn.execute("""
                INSERT INTO vendors
                (vendor_name, vendor_website, vendor_type, contact_email, contact_phone,
                 linkedin_url, relevance_score, event_id, status, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vendor.get('vendor_name'),
                vendor.get('vendor_website'),
                vendor.get('vendor_type', 'sponsor'),
                vendor.get('contact_email'),
                vendor.get('contact_phone'),
                vendor.get('linkedin_url'),
                float(vendor.get('relevance_score', 0) or 0),
                vendor.get('event_id'),
                vendor.get('status', 'identified'),
                now, now,
                json.dumps(metadata)
            ))
            return cursor.lastrowid
    
    def get_vendors(self, event_id: Optional[int] = None) -> List[Dict]:
        """Get vendors with optional filtering."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM vendors WHERE 1=1"
            params = []
            
            if event_id:
                query += " AND event_id = ?"
                params.append(event_id)
            
            query += " ORDER BY relevance_score DESC"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            vendors = []
            for row in rows:
                vendor = dict(row)
                vendor['metadata'] = json.loads(vendor.get('metadata', '{}'))
                vendors.append(vendor)
            
            return vendors
    
    def save_email(self, email: Dict) -> int:
        """Save an email draft."""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.utcnow().isoformat()
            
            metadata = {k: v for k, v in email.items()
                       if k not in ['id', 'recipient_type', 'recipient_id', 'subject',
                                   'body', 'status', 'gmail_draft_id']}
            
            cursor = conn.execute("""
                INSERT INTO emails
                (recipient_type, recipient_id, subject, body, status, gmail_draft_id,
                 created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email.get('recipient_type'),
                email.get('recipient_id'),
                email.get('subject'),
                email.get('body'),
                email.get('status', 'draft'),
                email.get('gmail_draft_id'),
                now, now,
                json.dumps(metadata)
            ))
            return cursor.lastrowid
    
    def create_checkpoint_review(self, pipeline_id: str, checkpoint_name: str) -> int:
        """Create a checkpoint review entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO checkpoint_reviews
                (pipeline_id, checkpoint_name, status, metadata)
                VALUES (?, ?, 'pending', '{}')
            """, (pipeline_id, checkpoint_name))
            return cursor.lastrowid
    
    def approve_checkpoint(self, review_id: int, reviewer: str, notes: str = ""):
        """Approve a checkpoint review."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE checkpoint_reviews
                SET status = 'approved',
                    approved_at = ?,
                    approved_by = ?,
                    reviewer_notes = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), reviewer, notes, review_id))
    
    def get_pending_checkpoints(self, pipeline_id: str) -> List[Dict]:
        """Get pending checkpoints for a pipeline."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM checkpoint_reviews WHERE pipeline_id = ? AND status = 'pending'",
                (pipeline_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_event_by_id(self, event_id: int) -> Optional[Dict]:
        """Get a single event by ID.

        Args:
            event_id: The event ID

        Returns:
            Event dictionary or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM events WHERE id = ?",
                (event_id,)
            )
            row = cursor.fetchone()
            if row:
                event = dict(row)
                event['metadata'] = json.loads(event.get('metadata', '{}'))
                return event
            return None

    def update_event(self, event_id: int, updates: Dict) -> bool:
        """Update an event with partial data.

        Args:
            event_id: The event ID to update
            updates: Dictionary of fields to update

        Returns:
            True if updated successfully, False if event not found
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if event exists
            cursor = conn.execute(
                "SELECT id FROM events WHERE id = ?",
                (event_id,)
            )
            if not cursor.fetchone():
                return False

            now = datetime.utcnow().isoformat()
            updates['updated_at'] = now

            # Build update query dynamically
            allowed_fields = [
                'event_name', 'event_website', 'city', 'country',
                'start_date', 'end_date', 'theme', 'organizer',
                'overall_score', 'priority_tier', 'status', 'updated_at'
            ]

            update_fields = []
            values = []
            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    if field == 'overall_score':
                        values.append(float(value) if value else 0)
                    else:
                        values.append(value)

            if not update_fields:
                return True  # Nothing to update

            values.append(event_id)
            query = f"UPDATE events SET {', '.join(update_fields)} WHERE id = ?"

            conn.execute(query, values)
            logger.info(f"Updated event {event_id}")
            return True

    def delete_event(self, event_id: int) -> bool:
        """Delete an event and its associated data.

        Args:
            event_id: The event ID to delete

        Returns:
            True if deleted successfully, False if event not found
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if event exists
            cursor = conn.execute(
                "SELECT id FROM events WHERE id = ?",
                (event_id,)
            )
            if not cursor.fetchone():
                return False

            # Delete associated emails
            conn.execute(
                "DELETE FROM emails WHERE recipient_type = 'event' AND recipient_id = ?",
                (event_id,)
            )

            # Delete associated vendors
            conn.execute(
                "DELETE FROM vendors WHERE event_id = ?",
                (event_id,)
            )

            # Delete the event
            conn.execute(
                "DELETE FROM events WHERE id = ?",
                (event_id,)
            )

            logger.info(f"Deleted event {event_id} and associated data")
            return True

    def get_email_count(self, status: Optional[str] = None) -> int:
        """Get total count of emails, optionally filtered by status.

        Args:
            status: Optional status filter ('draft', 'sent', 'scheduled')

        Returns:
            Count of emails
        """
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT COUNT(*) FROM emails"
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]

    def update_email_status(self, email_id: int, status: str, gmail_draft_id: Optional[str] = None) -> bool:
        """Update email status.

        Args:
            email_id: The email ID
            status: New status ('draft', 'sent', 'scheduled')
            gmail_draft_id: Optional Gmail draft ID

        Returns:
            True if updated successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.utcnow().isoformat()

            if gmail_draft_id:
                conn.execute(
                    """UPDATE emails SET status = ?, gmail_draft_id = ?, updated_at = ?
                       WHERE id = ?""",
                    (status, gmail_draft_id, now, email_id)
                )
            else:
                conn.execute(
                    "UPDATE emails SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, email_id)
                )
            return True


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
