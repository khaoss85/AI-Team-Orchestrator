#!/usr/bin/env python3

import re

text = "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot con target open-rate ≥ 30 % e Click-to-rate almeno del 10% in 6 settimane"

patterns = [
    r'(\d+)\s*(sequenc[ei]?)\s*(email)?',
    r'(\d+)\s*(sequenc[ei]?)',
    r'(\d+)\s+sequenc[ei]?',
    r'almeno\s+(\d+)\s+sequenc[ei]?',
    r'(\d+)\s+sequenze\s+email'
]

print(f"Text: {text}")
print(f"\nTesting patterns:")

for i, pattern in enumerate(patterns, 1):
    matches = re.findall(pattern, text, re.IGNORECASE)
    print(f"{i}. Pattern: {pattern}")
    print(f"   Matches: {matches}")