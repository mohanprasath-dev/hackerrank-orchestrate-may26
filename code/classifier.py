"""
Classifier module for support ticket triage.

Functions:
- get_request_type: Classify issue as product_issue, feature_request, bug, or invalid
- get_product_area: Map issue to product area based on company and content
"""

import re
from typing import Literal


def get_request_type(issue: str) -> Literal["product_issue", "feature_request", "bug", "invalid"]:
    """
    Classify the request type based on issue content.
    
    Priority order: invalid > bug > feature_request > product_issue
    
    Args:
        issue: The support ticket issue text
        
    Returns:
        One of: "product_issue", "feature_request", "bug", "invalid"
    """
    if not issue or not isinstance(issue, str):
        return "invalid"
    
    issue_lower = issue.lower().strip()
    
    # Check for invalid (harmful, gibberish, off-topic, malicious)
    invalid_patterns = [
        r'(virus|malware|hack|exploit|ddos|ransomware)',
        r'(hate|racist|slur)',
        r'(kill|murder|bomb|weapon)',
        r'^[a-z]{1,2}$',  # Single letters or 2-letter gibberish
        r'^[!@#$%^&*]{2,}$',  # Only special characters
        r'^(asdf|qwerty|hjkl|zxcv|xxx|aaa|bbb)$',  # Obvious gibberish
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, issue_lower):
            return "invalid"
    
    # Check if mostly incoherent (very short random words)
    if len(issue_lower) < 5 and not any(c.isalpha() for c in issue_lower):
        return "invalid"
    
    # Check for bug (highest priority after invalid)
    bug_keywords = [
        'not working', 'broken', 'error', 'down', 'stopped', 'crashing',
        "can't access", 'cannot access', 'crash', 'failed', 'failure',
        'issue', 'problem', 'bug', 'exception', 'error code', 'not responding',
        'won\'t load', 'won\'t open', 'stuck', 'hang', 'timeout',
        'broken link', 'page not found', '404', 'invalid request',
        'connection refused', 'connection timeout', 'service unavailable',
        'blank screen', 'white screen', 'black screen'
    ]
    
    if any(keyword in issue_lower for keyword in bug_keywords):
        return "bug"
    
    # Check for feature request
    feature_keywords = [
        'would like', 'can you add', 'request a feature', 'suggest',
        'wish', 'feature request', 'new feature', 'enhancement',
        'add support', 'add option', 'add capability', 'make it',
        'could you', 'would it be possible', 'please add',
        'it would be great', 'i wish', 'feature', 'request'
    ]
    
    if any(keyword in issue_lower for keyword in feature_keywords):
        return "feature_request"
    
    # Default to product_issue
    return "product_issue"


def get_product_area(
    issue: str,
    company: str,
    retrieved_chunks: list = None
) -> str:
    """
    Map issue to product area based on company and content.
    
    Args:
        issue: The support ticket issue text
        company: Company name (HackerRank, Claude, Visa, or None)
        retrieved_chunks: List of retrieved support articles (optional).
                         Each chunk should have a 'source' field with file path.
        
    Returns:
        Product area category as a string
    """
    if not issue or not isinstance(issue, str):
        return "general"
    
    issue_lower = issue.lower()
    retrieved_chunks = retrieved_chunks or []
    
    company_lower = (company or "").lower().strip()
    
    # Extract source paths from retrieved chunks to detect keywords
    source_keywords = set()
    for chunk in retrieved_chunks:
        if isinstance(chunk, dict) and 'source' in chunk:
            source = chunk['source'].lower()
            # Extract category from path (e.g., "data/claude/account-management/..." → "account-management")
            parts = source.split('/')
            source_keywords.update(parts)
    
    # ========== HackerRank ==========
    if 'hackerrank' in company_lower:
        # screen
        if any(kw in issue_lower for kw in ['screen', 'coding interview', 'code completion', 'test screen']):
            return "screen"
        if 'screen' in source_keywords:
            return "screen"
        
        # interviews
        if any(kw in issue_lower for kw in ['interview', 'candidate', 'interviewer', 'interview round', 'interview questions']):
            return "interviews"
        if 'interviews' in source_keywords:
            return "interviews"
        
        # library
        if any(kw in issue_lower for kw in ['library', 'problem', 'challenge', 'kata', 'exercises']):
            return "library"
        if 'library' in source_keywords:
            return "library"
        
        # engage
        if any(kw in issue_lower for kw in ['engage', 'recruitment', 'talent acquisition', 'hiring']):
            return "engage"
        if 'engage' in source_keywords:
            return "engage"
        
        # skillup
        if any(kw in issue_lower for kw in ['skillup', 'learning', 'course', 'training', 'certificate', 'track']):
            return "skillup"
        if 'skillup' in source_keywords:
            return "skillup"
        
        # integrations
        if any(kw in issue_lower for kw in ['integration', 'api', 'plugin', 'webhook', 'connect', 'third party']):
            return "integrations"
        if 'integrations' in source_keywords:
            return "integrations"
        
        # settings
        if any(kw in issue_lower for kw in ['settings', 'preferences', 'configuration', 'profile', 'account settings']):
            return "settings"
        if 'settings' in source_keywords:
            return "settings"
        
        return "general-help"
    
    # ========== Claude ==========
    if 'claude' in company_lower:
        # account-management
        if any(kw in issue_lower for kw in ['account', 'login', 'password', 'signup', 'subscription', 'plan']):
            return "account-management"
        if 'account-management' in source_keywords:
            return "account-management"
        
        # usage-and-limits
        if any(kw in issue_lower for kw in ['limit', 'rate limit', 'usage', 'quota', 'token', 'context window']):
            return "usage-and-limits"
        if 'usage-and-limits' in source_keywords:
            return "usage-and-limits"
        
        # troubleshooting
        if any(kw in issue_lower for kw in ['troubleshoot', 'debug', 'error', 'not working', 'problem', 'issue', 'fix']):
            return "troubleshooting"
        if 'troubleshooting' in source_keywords:
            return "troubleshooting"
        
        # team-and-enterprise-plans
        if any(kw in issue_lower for kw in ['team', 'enterprise', 'organization', 'collaboration', 'admin', 'user management']):
            return "team-and-enterprise-plans"
        if 'team-and-enterprise-plans' in source_keywords:
            return "team-and-enterprise-plans"
        
        # privacy-and-legal
        if any(kw in issue_lower for kw in ['privacy', 'gdpr', 'legal', 'terms', 'compliance', 'data', 'policy']):
            return "privacy-and-legal"
        if 'privacy-and-legal' in source_keywords:
            return "privacy-and-legal"
        
        # claude-api-and-console
        if any(kw in issue_lower for kw in ['api', 'console', 'integration', 'developer', 'code', 'programming']):
            return "claude-api-and-console"
        if 'claude-api-and-console' in source_keywords:
            return "claude-api-and-console"
        
        return "troubleshooting"
    
    # ========== Visa ==========
    if 'visa' in company_lower:
        # consumer
        if any(kw in issue_lower for kw in ['consumer', 'personal', 'credit card', 'debit card', 'individual', 'cardholder']):
            return "consumer"
        if 'consumer' in source_keywords:
            return "consumer"
        
        # small-business
        if any(kw in issue_lower for kw in ['small business', 'business', 'sme', 'smb', 'merchant', 'shop', 'store']):
            return "small-business"
        if 'small-business' in source_keywords:
            return "small-business"
        
        # merchant (fallback for payment/transaction topics)
        if any(kw in issue_lower for kw in ['merchant', 'payment', 'transaction', 'checkout', 'accept payment']):
            return "merchant"
        if 'merchant' in source_keywords:
            return "merchant"
        
        return "consumer"
    
    # ========== Default (company is None or unknown) ==========
    return "general"
