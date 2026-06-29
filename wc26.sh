#!/bin/bash
# wc26-bnaul Control Script
# All-in-one CLI controller for the ClawCup FIFA World Cup 2026 Agent
# Usage: ./wc26.sh [command] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Helper functions
print_header() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║           wc26-bnaul — ClawCup FIFA World Cup 2026 Agent             ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_section() {
    echo -e "\n${BOLD}${CYAN}$1${NC}"
    echo -e "${CYAN}$(printf '─%.0s' $(seq 1 70))${NC}"
}

# Check if uv is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed. Install it first:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
}

# Check if .env exists
check_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << 'EOF'
# Required: ClawCup API credentials
CLAWCUP_TOKEN="wca_..."
CLAWCUP_SIGNING_SECRET="wca_sec_..."

# Optional: External data APIs
FOOTBALL_DATA_API_KEY="your_key"    # football-data.org
API_FOOTBALL_KEY="your_key"          # API-Football (RapidAPI)
NEWSAPI_KEY="your_key"               # NewsAPI (newsapi.org)
EOF
        print_info "Please edit .env with your actual credentials"
        exit 1
    fi
}

# Show main menu
show_menu() {
    print_header
    echo -e "${BOLD}Available Commands:${NC}\n"
    
    echo -e "${GREEN}━━━ AGENT COMMANDS (Play the Game) ━━━${NC}"
    echo -e "  ${BOLD}me${NC}                    Show agent info and standings"
    echo -e "  ${BOLD}fixtures${NC}              List open fixtures"
    echo -e "  ${BOLD}predict${NC} <match_id>   Submit prediction for a match"
    echo -e "  ${BOLD}check${NC}                 Check all submitted predictions"
    echo -e "  ${BOLD}mine${NC} <match_id>      View specific prediction"
    echo -e "  ${BOLD}fifa-data${NC}             Fetch live FIFA data"
    echo ""
    
    echo -e "${YELLOW}━━━ ANALYSIS COMMANDS (Analyze Before Playing) ━━━${NC}"
    echo -e "  ${BOLD}predict-model${NC} <home> <away>  Run prediction model"
    echo -e "  ${BOLD}strategy-demo${NC}                  Show strategy demonstration"
    echo -e "  ${BOLD}backtest-demo${NC}                  Run backtest demonstration"
    echo ""
    
    echo -e "${BLUE}━━━ MONITORING COMMANDS (Set and Forget) ━━━${NC}"
    echo -e "  ${BOLD}monitor${NC}               Run news monitor (dry-run)"
    echo -e "  ${BOLD}monitor-live${NC}          Run news monitor (live resubmit)"
    echo -e "  ${BOLD}monitor-check${NC} <id>    Manual check specific match"
    echo ""
    
    echo -e "${CYAN}━━━ DEVELOPMENT COMMANDS ━━━${NC}"
    echo -e "  ${BOLD}test${NC}                  Run all tests"
    echo -e "  ${BOLD}test-v${NC}                Run tests with verbose output"
    echo -e "  ${BOLD}sync${NC}                  Sync dependencies (uv sync)"
    echo -e "  ${BOLD}shell${NC}                 Open uv shell"
    echo ""
    
    echo -e "${MAGENTA}━━━ UTILITY COMMANDS ━━━${NC}"
    echo -e "  ${BOLD}status${NC}                Show project status"
    echo -e "  ${BOLD}env-check${NC}             Check environment setup"
    echo -e "  ${BOLD}help${NC}                  Show this help message"
    echo ""
    
    echo -e "${BOLD}Examples:${NC}"
    echo "  ./wc26.sh me"
    echo "  ./wc26.sh predict m001 --prob 0.65 0.20 0.15"
    echo "  ./wc26.sh predict-model BRAZIL JAPAN"
    echo "  ./wc26.sh monitor"
    echo ""
}

# Show project status
show_status() {
    print_section "Project Status"
    
    # Check uv
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version 2>/dev/null | head -1)
        print_success "uv installed: $UV_VERSION"
    else
        print_error "uv not installed"
    fi
    
    # Check .env
    if [ -f ".env" ]; then
        print_success ".env file exists"
        
        # Check credentials
        if grep -q "CLAWCUP_TOKEN=" .env && grep -q "CLAWCUP_SIGNING_SECRET=" .env; then
            if grep -q 'CLAWCUP_TOKEN="wca_\.\.\."' .env || grep -q 'CLAWCUP_SIGNING_SECRET="wca_sec_\.\.\."' .env; then
                print_warning "ClawCup credentials are set to placeholder values"
            else
                print_success "ClawCup credentials configured"
            fi
        fi
        
        if grep -q "FOOTBALL_DATA_API_KEY=" .env && ! grep -q 'FOOTBALL_DATA_API_KEY="your_key"' .env; then
            print_success "football-data.org API key configured"
        else
            print_info "football-data.org API key not configured (optional)"
        fi
        
        if grep -q "API_FOOTBALL_KEY=" .env && ! grep -q 'API_FOOTBALL_KEY="your_key"' .env; then
            print_success "API-Football key configured"
        else
            print_info "API-Football key not configured (optional)"
        fi
        
        if grep -q "NEWSAPI_KEY=" .env && ! grep -q 'NEWSAPI_KEY="your_key"' .env; then
            print_success "NewsAPI key configured"
        else
            print_info "NewsAPI key not configured (optional)"
        fi
    else
        print_error ".env file not found"
    fi
    
    # Check Python files
    print_section "Source Files"
    for file in src/wc26_bnaul/__init__.py src/wc26_bnaul/predictor.py src/wc26_bnaul/fifa_data.py src/wc26_bnaul/news_monitor_real.py src/wc26_bnaul/strategy.py; do
        if [ -f "$file" ]; then
            print_success "$file"
        else
            print_error "$file missing"
        fi
    done
    
    # Check git
    print_section "Git Status"
    if [ -d ".git" ]; then
        BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
        COMMITS=$(git rev-list --count HEAD 2>/dev/null || echo "0")
        print_success "Git repo on branch: $BRANCH ($COMMITS commits)"
        
        # Check for uncommitted changes
        if git diff --quiet HEAD 2>/dev/null; then
            print_success "Working tree clean"
        else
            print_warning "Uncommitted changes detected"
            git status --short
        fi
    else
        print_error "Not a git repository"
    fi
}

# Check environment
env_check() {
    print_section "Environment Check"
    
    check_uv
    check_env
    
    print_success "Environment check passed"
    print_info "Run './wc26.sh status' for detailed status"
}

# Main command dispatcher
case "${1:-help}" in
    me)
        check_uv
        print_section "Agent Info"
        uv run wc26-bnaul me
        ;;
    
    fixtures)
        check_uv
        print_section "Open Fixtures"
        uv run wc26-bnaul fixtures --status=open
        ;;
    
    predict)
        check_uv
        if [ -z "$2" ]; then
            print_error "Usage: ./wc26.sh predict <match_id> [options]"
            echo ""
            echo "Examples:"
            echo "  ./wc26.sh predict m001 --prob 0.65 0.20 0.15 --reasoning 'Brazil strong' --score 2-1"
            echo "  ./wc26.sh predict m074 --binary 0.88 0.12 --reasoning 'Brazil advance' --score 2-0"
            exit 1
        fi
        MATCH_ID=$2
        shift 2
        print_section "Submit Prediction: $MATCH_ID"
        uv run wc26-bnaul predict "$MATCH_ID" "$@"
        ;;
    
    check)
        check_uv
        print_section "My Predictions"
        uv run wc26-bnaul check
        ;;
    
    mine)
        check_uv
        if [ -z "$2" ]; then
            print_error "Usage: ./wc26.sh mine <match_id>"
            exit 1
        fi
        print_section "Prediction: $2"
        uv run wc26-bnaul mine "$2"
        ;;
    
    fifa-data)
        check_uv
        print_section "FIFA Data"
        uv run wc26-bnaul fifa-data --source api-football --live
        ;;
    
    predict-model)
        check_uv
        if [ -z "$2" ] || [ -z "$3" ]; then
            print_error "Usage: ./wc26.sh predict-model <home_team> <away_team>"
            echo ""
            echo "Example:"
            echo "  ./wc26.sh predict-model BRAZIL JAPAN"
            exit 1
        fi
        print_section "Prediction Model: $2 vs $3"
        uv run wc26-bnaul predict-model "$2" "$3" --fifa-rank-home 6 --fifa-rank-away 18 --form-home 4 --form-away 3
        ;;
    
    strategy-demo)
        check_uv
        print_section "Strategy Demonstration"
        uv run wc26-bnaul strategy-demo
        ;;
    
    backtest-demo)
        check_uv
        print_section "Backtest Demonstration"
        uv run wc26-bnaul backtest-demo
        ;;
    
    monitor)
        check_uv
        print_section "News Monitor (Dry Run)"
        print_warning "This will check for news but NOT submit predictions"
        print_info "Press Ctrl+C to stop"
        echo ""
        uv run python -m wc26_bnaul.news_monitor_real --dry-run --interval 300
        ;;
    
    monitor-live)
        check_uv
        print_section "News Monitor (LIVE)"
        print_error "WARNING: This will actually resubmit predictions based on news!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            uv run python -m wc26_bnaul.news_monitor_real --interval 300
        else
            print_info "Cancelled"
        fi
        ;;
    
    monitor-check)
        check_uv
        if [ -z "$2" ]; then
            print_error "Usage: ./wc26.sh monitor-check <match_id>"
            exit 1
        fi
        print_section "Manual Check: $2"
        uv run python -m wc26_bnaul.news_monitor_real --check "$2" --dry-run
        ;;
    
    test)
        check_uv
        print_section "Running Tests"
        uv run pytest tests/
        ;;
    
    test-v)
        check_uv
        print_section "Running Tests (Verbose)"
        uv run pytest tests/ -v
        ;;
    
    sync)
        print_section "Syncing Dependencies"
        uv sync
        print_success "Dependencies synced"
        ;;
    
    shell)
        print_section "Opening uv Shell"
        print_info "Type 'exit' to leave the shell"
        uv run bash
        ;;
    
    status)
        show_status
        ;;
    
    env-check)
        env_check
        ;;
    
    help|--help|-h)
        show_menu
        ;;
    
    *)
        print_error "Unknown command: $1"
        echo ""
        show_menu
        exit 1
        ;;
esac
