"""LLM Helper utilities for agent implementations."""

import json
import logging
from typing import Dict, Any, Optional, Type, Callable
from pydantic import BaseModel

from utils.configurable_llm_client import LLMResponse

logger = logging.getLogger(__name__)


def extract_json_from_response(content: str) -> Optional[Dict]:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in markdown code blocks
    if "```json" in content:
        start = content.find("```json") + 7
        end = content.find("```", start)
        if end > start:
            json_str = content[start:end].strip()
            return json.loads(json_str)
    
    # Try to find JSON in generic code blocks
    if "```" in content:
        start = content.find("```") + 3
        end = content.find("```", start)
        if end > start:
            json_str = content[start:end].strip()
            return json.loads(json_str)
    
    # Try to parse entire content as JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON between curly braces
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(content[start:end+1])
        except json.JSONDecodeError:
            pass
    
    logger.warning(f"Could not extract JSON from response: {content[:200]}...")
    return None


def llm_call_with_json_output(
    llm_func: Callable,
    prompt: str,
    system_message: str,
    response_schema: Optional[Type[BaseModel]] = None,
    max_retries: int = 2
) -> Optional[Dict]:
    """Call LLM and parse JSON output with retry logic.
    
    Args:
        llm_func: The LLM callable from BaseAgent.llm
        prompt: User prompt
        system_message: System message for context
        response_schema: Optional Pydantic model for schema validation
        max_retries: Number of retries on failure
    
    Returns:
        Parsed JSON dict or None if all retries fail
    """
    response_format = None
    if response_schema:
        response_format = {"type": "json_object"}
    
    for attempt in range(max_retries + 1):
        try:
            response: LLMResponse = llm_func(
                prompt=prompt,
                system_message=system_message,
                response_format=response_format
            )
            
            if not response.success:
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {response.error}")
                continue
            
            data = extract_json_from_response(response.content)
            if data is not None:
                if response_schema:
                    # Validate against schema
                    try:
                        validated = response_schema(**data)
                        return validated.dict()
                    except Exception as e:
                        logger.warning(f"Schema validation failed: {e}")
                        return data  # Return raw data anyway
                return data
            
        except Exception as e:
            logger.error(f"LLM call exception (attempt {attempt + 1}): {e}")
    
    return None


def llm_call_with_fallback(
    llm_func: Callable,
    prompt: str,
    system_message: str,
    fallback_value: Any,
    max_retries: int = 2
) -> Any:
    """Call LLM with automatic fallback on failure.
    
    Args:
        llm_func: The LLM callable
        prompt: User prompt
        system_message: System message
        fallback_value: Value to return if LLM fails
        max_retries: Number of retries
    
    Returns:
        LLM response content or fallback value
    """
    for attempt in range(max_retries + 1):
        try:
            response: LLMResponse = llm_func(
                prompt=prompt,
                system_message=system_message
            )
            
            if response.success and response.content:
                return response.content
            
            logger.warning(f"LLM call returned no content (attempt {attempt + 1})")
            
        except Exception as e:
            logger.error(f"LLM call exception (attempt {attempt + 1}): {e}")
    
    return fallback_value


# Common system messages for agents
INTENT_UNDERSTANDING_SYSTEM = """You are an expert at understanding user intent for event marketing and sponsorship research.
Your task is to analyze natural language queries and extract structured intent information.
Always respond with valid JSON."""

EVENT_DISCOVERY_SYSTEM = """You are an expert event researcher specializing in finding industry conferences, summits, and trade shows.
You analyze search results and extract structured event information with high accuracy.
Always respond with valid JSON."""

VENDOR_DISCOVERY_SYSTEM = """You are an expert at identifying service providers, vendors, and contractors for events.
You analyze web content and extract vendor information including services offered and contact details.
Always respond with valid JSON."""

EVENT_INTELLIGENCE_SYSTEM = """You are a strategic marketing analyst specializing in event sponsorship ROI analysis.
You provide strategic insights about events including audience analysis, competitor presence, and sponsorship recommendations.
Always respond with valid JSON."""

OUTREACH_EMAIL_SYSTEM = """You are an expert B2B marketing copywriter specializing in sponsorship outreach.
You write compelling, personalized emails that get responses from event organizers.
Be professional, concise, and value-focused."""

EVENT_QUALIFICATION_SYSTEM = """You are an expert at evaluating events for sponsorship potential.
You score events based on audience quality, industry relevance, ROI potential, and strategic fit.
Always provide detailed reasoning for your scores."""

EVENT_PRIORITIZATION_SYSTEM = """You are an expert at prioritizing marketing investments.
You rank events by ROI potential and provide clear recommendations on which events to sponsor.
Always justify your rankings with data-driven reasoning."""
