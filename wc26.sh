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

# Show interactive menu
show_interactive_menu() {
    print_header
    echo -e "${BOLD}Select a command:${NC}\n"
    
    echo -e "${GREEN}[1]${NC} ${BOLD}me${NC}                    — Show agent info and standings"
    echo -e "${GREEN}[2]${NC} ${BOLD}fixtures${NC}              — List open fixtures"
    echo -e "${GREEN}[3]${NC} ${BOLD}predict${NC} <match_id>   — Submit prediction for a match"
    echo -e "${GREEN}[4]${NC} ${BOLD}check${NC}                 — Check all submitted predictions"
    echo -e "${GREEN}[5]${NC} ${BOLD}mine${NC} <match_id>      — View specific prediction"
    echo -e "${GREEN}[6]${NC} ${BOLD}fifa-data${NC}             — Fetch live FIFA data"
    echo ""
    
    echo -e "${YELLOW}[7]${NC}  ${BOLD}predict-model${NC} <home> <away>  — Run prediction model"
    echo -e "${YELLOW}[8]${NC}  ${BOLD}strategy-demo${NC}                  — Show strategy demonstration"
    echo -e "${YELLOW}[9]${NC}  ${BOLD}backtest-demo${NC}                  — Run backtest demonstration"
    echo ""
    
    echo -e "${BLUE}[10]${NC} ${BOLD}monitor${NC}               — Run news monitor (dry-run)"
    echo -e "${BLUE}[11]${NC} ${BOLD}monitor-live${NC}          — Run news monitor (live resubmit)"
    echo -e "${BLUE}[12]${NC} ${BOLD}monitor-check${NC} <id>    — Manual check specific match"
    echo ""
    
    echo -e "${RED}[19]${NC} ${BOLD}run${NC} <match_id>          — FULL PIPELINE: news → model → submit"
    echo -e "${MAGENTA}[20]${NC} ${BOLD}performance${NC}           — View prediction accuracy & Brier scores"
    echo -e "${MAGENTA}[21]${NC} ${BOLD}suggest-weights${NC}         — Get weight updates based on history"
    echo -e "${MAGENTA}[22]${NC} ${BOLD}auto-agent${NC}            — Auto predict all open matches (dry-run)"
    echo -e "${MAGENTA}[23]${NC} ${BOLD}auto-agent-live${NC}       — Auto predict and submit (LIVE)"
    echo ""
    
    echo -e "${CYAN}[13]${NC} ${BOLD}test${NC}                  — Run all tests"
    echo -e "${CYAN}[14]${NC} ${BOLD}test-v${NC}                — Run tests with verbose output"
    echo -e "${CYAN}[15]${NC} ${BOLD}sync${NC}                  — Sync dependencies (uv sync)"
    echo -e "${CYAN}[16]${NC} ${BOLD}shell${NC}                 — Open uv shell"
    echo ""
    
    echo -e "${MAGENTA}[17]${NC} ${BOLD}status${NC}                — Show project status"
    echo -e "${MAGENTA}[18]${NC} ${BOLD}env-check${NC}             — Check environment setup"
    echo -e "${MAGENTA}[0]${NC}  ${BOLD}quit${NC}                  — Exit"
    echo ""
}

# Show quick help
show_quick_help() {
    echo -e "${BOLD}Usage:${NC} ./wc26.sh [command] [options]"
    echo ""
    echo -e "${GREEN}Agent:${NC} me, fixtures, predict <id>, check, mine <id>, fifa-data"
    echo -e "${YELLOW}Analysis:${NC} predict-model <h> <a>, strategy-demo, backtest-demo"
    echo -e "${BLUE}Monitor:${NC} monitor, monitor-live, monitor-check <id>"
    echo -e "${CYAN}Dev:${NC} test, test-v, sync, shell"
    echo -e "${MAGENTA}Utility:${NC} status, env-check, help"
    echo ""
    echo -e "${RED}Pipeline:${NC} run <match_id> — Full pipeline: news → model → submit"
    echo ""
    echo "Run without arguments for interactive menu."
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

# Full pipeline: news → model → submit
run_pipeline() {
    local match_id="$1"
    
    if [ -z "$match_id" ]; then
        print_error "Usage: ./wc26.sh run <match_id>"
        echo ""
        echo "Example:"
        echo "  ./wc26.sh run m001"
        exit 1
    fi
    
    print_header
    print_section "FULL PIPELINE: $match_id"
    print_info "Steps: 1.Fetch News → 2.Run Model → 3.Analyze → 4.Submit"
    echo ""
    
    # Step 1: Fetch match details
    print_section "Step 1/4: Fetch Match Details"
    local fixtures_json
    fixtures_json=$(uv run python -c "
import sys, json
from wc26_bnaul import api_request
try:
    data = api_request('GET', '/fixtures?status=open')
    matches = data.get('matches', [])
    for m in matches:
        if m['match_id'] == '$match_id':
            print(json.dumps(m))
            sys.exit(0)
    print('{}')
except Exception as e:
    print('{}')
" 2>/dev/null)
    
    if [ "$fixtures_json" = "{}" ] || [ -z "$fixtures_json" ]; then
        print_error "Match $match_id not found or not open"
        exit 1
    fi
    
    local home away kickoff
    home=$(echo "$fixtures_json" | uv run python -c "import sys, json; print(json.load(sys.stdin).get('home', 'UNKNOWN'))")
    away=$(echo "$fixtures_json" | uv run python -c "import sys, json; print(json.load(sys.stdin).get('away', 'UNKNOWN'))")
    kickoff=$(echo "$fixtures_json" | uv run python -c "import sys, json; print(json.load(sys.stdin).get('kickoff_utc', 'UNKNOWN'))")
    
    print_success "Match: $home vs $away"
    print_info "Kickoff: $kickoff"
    echo ""
    
    # Step 2: Check news & injuries
    print_section "Step 2/4: Check News & Injuries"
    uv run python -m wc26_bnaul.news_monitor_real --check "$match_id" --dry-run
    echo ""
    
    # Step 3: Run ensemble prediction model and capture output
    print_section "Step 3/4: Run Ensemble Prediction Model"
    print_info "Running: ensemble predictor with xG + Elo + form + H2H + injuries"
    
    # Run ensemble model and capture binary probabilities
    local ensemble_output
    ensemble_output=$(uv run python -c "
import sys
sys.path.insert(0, 'src')
from wc26_bnaul.ensemble_predictor import EnsemblePredictor
from wc26_bnaul.batch_predict import get_team_data

# Get team data from database
home_data = get_team_data('$home')
away_data = get_team_data('$away')

predictor = EnsemblePredictor()
result = predictor.predict(
    home_team='$home',
    away_team='$away',
    home_rank=home_data['rank'],
    away_rank=away_data['rank'],
    home_xg=home_data['xg'],
    home_xga=home_data['xga'],
    away_xg=away_data['xg'],
    away_xga=away_data['xga'],
    home_form=home_data['form'],
    away_form=away_data['form'],
    knockout=True,
)

print(f'Home win: {result.home_win_prob:.0%}')
print(f'Draw: {result.draw_prob:.0%}')
print(f'Away win: {result.away_win_prob:.0%}')
print(f'Expected score: {result.most_likely_score}')
print(f'Confidence: {result.confidence:.0%}')
print(f'Components: {result.ensemble_components}')

binary = result.to_binary()
print(f'BINARY_PROB:{binary[0]:.2f},{binary[1]:.2f}')
print(f'SCORE:{result.most_likely_score}')
")
    
    echo "$ensemble_output"
    echo ""
    
    # Extract binary probabilities and score from output
    local home_prob away_prob score
    home_prob=$(echo "$ensemble_output" | grep "BINARY_PROB:" | sed 's/BINARY_PROB://' | cut -d',' -f1)
    away_prob=$(echo "$ensemble_output" | grep "BINARY_PROB:" | sed 's/BINARY_PROB://' | cut -d',' -f2)
    score=$(echo "$ensemble_output" | grep "SCORE:" | sed 's/SCORE://')
    
    # Step 4: Auto-submit with confirmation
    print_section "Step 4/4: Submit Prediction"
    print_info "Auto-generated from ensemble model:"
    print_info "Home: $home_prob, Away: $away_prob"
    print_info "Score: $score"
    echo ""
    
    echo -n "Submit prediction? (yes/no/dry-run): "
    read -r confirm
    
    case "$confirm" in
        yes|y)
            print_section "Submitting..."
            local reasoning="Ensemble: xG+Elo+Form+H2H+Injury — $home $home_prob vs $away $away_prob"
            uv run wc26-bnaul predict "$match_id" --binary "$home_prob" "$away_prob" --reasoning "$reasoning" --score "$score"
            print_success "Prediction submitted!"
            ;;
        dry-run|d)
            print_section "Dry Run"
            print_info "Would submit:"
            echo "  Match: $match_id — $home vs $away"
            echo "  Probability: $home_prob / $away_prob"
            echo "  Score: $score"
            ;;
        *)
            print_info "Cancelled"
            ;;
    esac
}

# Interactive mode
run_interactive() {
    while true; do
        show_interactive_menu
        echo -n "Enter choice [0-18]: "
        read -r choice
        
        case "$choice" in
            1)
                check_uv
                print_section "Agent Info"
                uv run wc26-bnaul me
                ;;
            2)
                check_uv
                print_section "Open Fixtures"
                uv run wc26-bnaul fixtures --status=open
                ;;
            3)
                check_uv
                echo -n "Enter match ID (e.g., m001): "
                read -r match_id
                echo -n "Enter probabilities (e.g., 0.65 0.20 0.15): "
                read -r probs
                echo -n "Enter reasoning: "
                read -r reasoning
                echo -n "Enter score prediction (e.g., 2-1): "
                read -r score
                print_section "Submit Prediction: $match_id"
                uv run wc26-bnaul predict "$match_id" --prob $probs --reasoning "$reasoning" --score "$score"
                ;;
            4)
                check_uv
                print_section "My Predictions"
                uv run wc26-bnaul check
                ;;
            5)
                check_uv
                echo -n "Enter match ID: "
                read -r match_id
                print_section "Prediction: $match_id"
                uv run wc26-bnaul mine "$match_id"
                ;;
            6)
                check_uv
                print_section "FIFA Data"
                uv run wc26-bnaul fifa-data --source api-football --live
                ;;
            7)
                check_uv
                echo -n "Enter home team (e.g., BRAZIL): "
                read -r home
                echo -n "Enter away team (e.g., JAPAN): "
                read -r away
                print_section "Prediction Model: $home vs $away"
                uv run wc26-bnaul predict-model "$home" "$away" --fifa-rank-home 6 --fifa-rank-away 18 --form-home 4 --form-away 3
                ;;
            8)
                check_uv
                print_section "Strategy Demonstration"
                uv run wc26-bnaul strategy-demo
                ;;
            9)
                check_uv
                print_section "Backtest Demonstration"
                uv run wc26-bnaul backtest-demo
                ;;
            10)
                check_uv
                print_section "News Monitor (Dry Run)"
                print_warning "This will check for news but NOT submit predictions"
                print_info "Press Ctrl+C to stop"
                echo ""
                uv run python -m wc26_bnaul.news_monitor_real --dry-run --interval 300
                ;;
            11)
                check_uv
                print_section "News Monitor (LIVE)"
                print_error "WARNING: This will actually resubmit predictions based on news!"
                echo -n "Are you sure? (yes/no): "
                read -r confirm
                if [ "$confirm" = "yes" ]; then
                    uv run python -m wc26_bnaul.news_monitor_real --interval 300
                else
                    print_info "Cancelled"
                fi
                ;;
            12)
                check_uv
                echo -n "Enter match ID: "
                read -r match_id
                print_section "Manual Check: $match_id"
                uv run python -m wc26_bnaul.news_monitor_real --check "$match_id" --dry-run
                ;;
            19)
                check_uv
                echo -n "Enter match ID (e.g., m001): "
                read -r match_id
                run_pipeline "$match_id"
                ;;
            20)
                check_uv
                print_section "Prediction Performance"
                uv run wc26-bnaul performance
                ;;
            21)
                check_uv
                print_section "Suggested Weight Updates"
                uv run wc26-bnaul suggest-weights
                ;;
            22)
                check_uv
                print_section "Auto Agent — All Open Matches"
                uv run wc26-bnaul auto-agent --dry-run
                ;;
            23)
                check_uv
                print_error "WARNING: This will auto-submit predictions!"
                echo -n "Are you sure? (yes/no): "
                read -r confirm
                if [ "$confirm" = "yes" ]; then
                    uv run wc26-bnaul auto-agent --live
                else
                    print_info "Cancelled"
                fi
                ;;
            13)
                check_uv
                print_section "Running Tests"
                uv run pytest tests/
                ;;
            14)
                check_uv
                print_section "Running Tests (Verbose)"
                uv run pytest tests/ -v
                ;;
            15)
                print_section "Syncing Dependencies"
                uv sync
                print_success "Dependencies synced"
                ;;
            16)
                print_section "Opening uv Shell"
                print_info "Type 'exit' to leave the shell"
                uv run bash
                ;;
            17)
                show_status
                ;;
            18)
                env_check
                ;;
            0|q|quit|exit)
                echo -e "\n${GREEN}Goodbye! 👋${NC}"
                exit 0
                ;;
            *)
                print_error "Invalid choice: $choice"
                ;;
        esac
        
        echo ""
        echo -n "Press Enter to continue..."
        read -r
    done
}

# Main command dispatcher
case "${1:-}" in
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
    
    run)
        check_uv
        run_pipeline "$2"
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
    
    performance)
        check_uv
        print_section "Prediction Performance"
        uv run wc26-bnaul performance
        ;;
    
    suggest-weights)
        check_uv
        print_section "Suggested Weight Updates"
        uv run wc26-bnaul suggest-weights
        ;;
    
    auto-agent)
        check_uv
        if [ -z "$2" ]; then
            print_section "Auto Agent — All Open Matches"
            uv run wc26-bnaul auto-agent --dry-run
        else
            print_section "Auto Agent — Match $2"
            uv run wc26-bnaul auto-agent --match "$2" --dry-run
        fi
        ;;
    
    auto-agent-live)
        check_uv
        print_error "WARNING: This will auto-submit predictions without confirmation!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            if [ -z "$2" ]; then
                print_section "Auto Agent LIVE — All Open Matches"
                uv run wc26-bnaul auto-agent --live
            else
                print_section "Auto Agent LIVE — Match $2"
                uv run wc26-bnaul auto-agent --match "$2" --live
            fi
        else
            print_info "Cancelled"
        fi
        ;;
    
    help|--help|-h)
        show_quick_help
        ;;
    
    "")
        # No arguments — run interactive mode
        run_interactive
        ;;
    
    *)
        print_error "Unknown command: $1"
        echo ""
        show_quick_help
        exit 1
        ;;
esac
