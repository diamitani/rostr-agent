#!/bin/bash
# ============================================================================
# ROSTR Agent Setup Script
# ============================================================================
# Quick setup for ROSTR framework combining Hermes Agent runtime with
# ROSTR intelligence layer (PAL, NPAO, RAG DAL, Hub).
#
# Usage:
#   ./setup-rostr.sh
#
# This script:
# 1. Detects desktop/server vs Android/Termux setup path
# 2. Creates a Python 3.11 virtual environment
# 3. Installs dependencies
# 4. Creates .env from template (if not exists)
# 5. Symlinks the 'rostr-agent' CLI command into a user-facing bin dir
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export UV_NO_CONFIG=1
PYTHON_VERSION="3.11"

is_termux() {
    [ -n "${TERMUX_VERSION:-}" ] || [[ "${PREFIX:-}" == *"com.termux/files/usr"* ]]
}

get_command_link_dir() {
    if is_termux && [ -n "${PREFIX:-}" ]; then
        echo "$PREFIX/bin"
    else
        echo "$HOME/.local/bin"
    fi
}

get_command_link_display_dir() {
    if is_termux && [ -n "${PREFIX:-}" ]; then
        echo "$PREFIX/bin"
    else
        echo "$HOME/.local/bin (add to PATH if needed)"
    fi
}

echo -e "${CYAN}=====================================${NC}"
echo -e "${CYAN}  ROSTR Agent Setup${NC}"
echo -e "${CYAN}=====================================${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

PYTHON_PATH=$(python3 -c "import sys; print(sys.executable)")
echo -e "${GREEN}✓ Found Python:${NC} $PYTHON_PATH"

# Create venv
echo -e "${YELLOW}→ Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${GREEN}✓ Virtual environment created${NC}"

# Upgrade pip
echo -e "${YELLOW}→ Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# Install dependencies
echo -e "${YELLOW}→ Installing ROSTR dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
else
    # Fallback: install core dependencies
    pip install anthropic>=0.87 pydantic>=2.0 pyyaml requests click > /dev/null 2>&1
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env if missing
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}→ Creating .env from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env created (edit with your API keys)${NC}"
    fi
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Create CLI symlink
CMD_DIR=$(get_command_link_dir)
mkdir -p "$CMD_DIR"

CLI_TARGET="$SCRIPT_DIR/rostr_cli.py"
if [ ! -f "$CLI_TARGET" ]; then
    echo -e "${RED}✗ rostr_cli.py not found${NC}"
    exit 1
fi

# Create wrapper script
WRAPPER="$CMD_DIR/rostr-agent"
cat > "$WRAPPER" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Find rostr repo
if [ -f "$REPO_DIR/rostr_cli.py" ]; then
    ROSTR_DIR="$REPO_DIR"
elif [ -f "./rostr_cli.py" ]; then
    ROSTR_DIR="$(pwd)"
else
    echo "Error: Could not find rostr installation"
    exit 1
fi

cd "$ROSTR_DIR"
source venv/bin/activate 2>/dev/null || true
python3 rostr_cli.py "$@"
EOF

chmod +x "$WRAPPER"

echo -e "${GREEN}✓ CLI symlink created${NC}"
echo -e "  Location: ${CYAN}$WRAPPER${NC}"
echo ""

# Summary
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Setup complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Test: ${CYAN}rostr-agent --version${NC}"
echo "3. List skills: ${CYAN}rostr-agent skills list${NC}"
echo "4. Run evaluation: ${CYAN}rostr-agent eval run${NC}"
echo ""
