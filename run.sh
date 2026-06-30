#!/bin/bash
# run.sh - Simple launcher for DDOS.py
# Usage: bash run.sh
# GitHub: https://github.com/cluod-s4/DDOS-CLOUD

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

clear

echo -e "${RED}${BOLD}"
echo -e "    ╔═══════════════════════════════════════╗"
echo -e "    ║                                       ║"
echo -e "    ║     ██████╗ ██████╗  ██████╗ ███████╗ ║"
echo -e "    ║     ██╔══██╗██╔══██╗██╔═══██╗██╔════╝ ║"
echo -e "    ║     ██║  ██║██████╔╝██║   ██║███████╗ ║"
echo -e "    ║     ██║  ██║██╔══██╗██║   ██║╚════██║ ║"
echo -e "    ║     ██████╔╝██║  ██║╚██████╔╝███████║ ║"
echo -e "    ║     ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝ ║"
echo -e "    ║                                       ║"
echo -e "    ╚═══════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${WHITE}${DIM}                      ╔══════════════════════════════╗${NC}"
echo -e "${WHITE}${DIM}                      ║     ${NC}${WHITE}From cloud${WHITE}${DIM}                ║${NC}"
echo -e "${WHITE}${DIM}                      ╚══════════════════════════════╝${NC}"
echo -e "${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}              DEPLOYMENT ENGINE v2099.99              ${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════${NC}"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] ROOT REQUIRED${NC}"
    echo -e "${YELLOW}[*] Restarting with sudo...${NC}"
    exec sudo bash "$0" "$@"
    exit 1
fi
echo -e "${GREEN}[✓] Root privileges confirmed${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[*] Installing Python3...${NC}"
    apt-get update -qq && apt-get install -y python3 python3-pip 2>/dev/null || \
    yum install -y python3 python3-pip 2>/dev/null || \
    { echo -e "${RED}[!] Python3 installation failed${NC}"; exit 1; }
fi
echo -e "${GREEN}[✓] Python3: $(python3 --version)${NC}"

echo -e "${YELLOW}[*] Installing dependencies...${NC}"
pip3 install --quiet scapy aiohttp dnspython psutil 2>/dev/null || \
pip install --quiet scapy aiohttp dnspython psutil 2>/dev/null
echo -e "${GREEN}[✓] Dependencies installed${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/DDOS.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}[!] DDOS.py not found in current directory${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] Starting DDOS engine...${NC}"
echo ""
python3 "$PYTHON_SCRIPT"
