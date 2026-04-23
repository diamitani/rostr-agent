#!/usr/bin/env bash
# ============================================================
# ROSTR Agent Framework — One-Click Setup
# ============================================================
set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
GOLD="\033[0;33m"
RESET="\033[0m"

echo -e "${BOLD}${GOLD}"
echo "  ██████╗  ██████╗ ███████╗████████╗██████╗ "
echo "  ██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝██╔══██╗"
echo "  ██████╔╝██║   ██║███████╗   ██║   ██████╔╝"
echo "  ██╔══██╗██║   ██║╚════██║   ██║   ██╔══██╗"
echo "  ██║  ██║╚██████╔╝███████║   ██║   ██║  ██║"
echo "  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝"
echo -e "${RESET}${BOLD}  Agent OS — One-Click Setup${RESET}"
echo ""

# ── Check Node.js ────────────────────────────────────────
echo -e "${BOLD}Checking prerequisites...${RESET}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found. Install Node.js 22+:${RESET}"
    echo -e "  ${YELLOW}https://nodejs.org/${RESET}"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo -e "${YELLOW}⚠ Node.js $NODE_VERSION detected. Node 22+ recommended.${RESET}"
else
    echo -e "${GREEN}✓ Node.js $(node -v)${RESET}"
fi

if command -v npm &> /dev/null; then
    echo -e "${GREEN}✓ npm $(npm -v)${RESET}"
fi

# ── Install Dependencies ─────────────────────────────────
echo ""
echo -e "${BOLD}Installing dependencies...${RESET}"
npm install --silent 2>/dev/null || npm install
echo -e "${GREEN}✓ Dependencies installed${RESET}"

# ── Environment Setup ─────────────────────────────────────
echo ""
echo -e "${BOLD}Setting up environment...${RESET}"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env from .env.example${RESET}"
else
    echo -e "${GREEN}✓ .env already exists${RESET}"
fi

# ── API Key Setup ─────────────────────────────────────────
echo ""
echo -e "${BOLD}API Key Setup ${RESET}${YELLOW}(press Enter to skip each)${RESET}"
echo ""

prompt_key() {
    local key_name="$1"
    local provider="$2"
    local placeholder="$3"
    echo -n "  $provider API key: "
    read -r key_val
    if [ -n "$key_val" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^${key_name}=.*|${key_name}=${key_val}|" .env
        else
            sed -i "s|^${key_name}=.*|${key_name}=${key_val}|" .env
        fi
        echo -e "  ${GREEN}✓ Set${RESET}"
    else
        echo -e "  ${YELLOW}Skipped${RESET}"
    fi
}

prompt_key "OPENAI_API_KEY" "OpenAI (recommended)" "sk-..."
prompt_key "ANTHROPIC_API_KEY" "Anthropic (Claude)" "sk-ant-..."
prompt_key "GROQ_API_KEY" "Groq (fast, free)" "gsk_..."

# ── Initialize Brain ─────────────────────────────────────
echo ""
echo -e "${BOLD}Initializing brain...${RESET}"
npx tsx src/cli/index.ts init 2>/dev/null || echo -e "${YELLOW}⚠ Brain init will complete on first run${RESET}"

# ── Done ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}✓ ROSTR is ready!${RESET}"
echo ""
echo -e "  ${CYAN}Start agent:${RESET}     npx tsx src/cli/index.ts serve"
echo -e "  ${CYAN}Chat:${RESET}            npx tsx src/cli/index.ts chat -i"
echo -e "  ${CYAN}Health check:${RESET}    npx tsx src/cli/index.ts doctor"
echo -e "  ${CYAN}Search brain:${RESET}    npx tsx src/cli/index.ts search \"query\""
echo ""
echo -e "${YELLOW}Dashboard: cd dashboard && npm install && npm run dev${RESET}"
echo -e "${YELLOW}API: http://localhost:3001/api/status${RESET}"
echo ""
