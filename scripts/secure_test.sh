#!/bin/bash

# Secure testing script with masked API key
# Usage: ./scripts/secure_test.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if API key is set
if [ -z "$GRID_AI_API_KEY" ]; then
    echo -e "${RED}Error: GRID_AI_API_KEY not set${NC}"
    echo "Set it with: export GRID_AI_API_KEY='your-key'"
    exit 1
fi

# Mask the API key for display
MASKED_KEY="${GRID_AI_API_KEY:0:8}...${GRID_AI_API_KEY: -4}"
echo -e "${GREEN}✓ API Key configured${NC} (masked: $MASKED_KEY)"
echo ""

# Run tests with masked output
python3 << 'PYTHON_SCRIPT'
import os
import sys
sys.path.insert(0, '.')

# Mask API key in any output
class MaskedOutput:
    def __init__(self, original_stream):
        self.original = original_stream
        self.key = os.environ.get('GRID_AI_API_KEY', '')
        self.masked = self.key[:8] + '...' + self.key[-4:] if len(self.key) > 12 else '***'
    
    def write(self, text):
        if self.key:
            text = text.replace(self.key, self.masked)
        self.original.write(text)
    
    def flush(self):
        self.original.flush()

sys.stdout = MaskedOutput(sys.stdout)
sys.stderr = MaskedOutput(sys.stderr)

# Run test
from utils.configurable_llm_client import get_llm_client
client = get_llm_client()

print("Testing Grid AI connection...")
response = client.complete_for_agent(
    agent_name="intent_understanding",
    prompt="Reply OK if you receive this.",
    system_message="Reply with OK only."
)

if response.success:
    print(f"✓ Connection successful")
    print(f"  Model: {response.model}")
    print(f"  Latency: {response.latency_ms}ms")
else:
    print(f"✗ Connection failed: {response.error}")
    exit(1)
PYTHON_SCRIPT

