#!/bin/bash
# template-processor.sh - Process XML templates with .env variables

set -e  # Exit on error

# Get the project root (two levels up from .claude/utils/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default values (relative to project root)
TEMPLATE_DIR="$PROJECT_ROOT/.claude/templates"
ENV_FILE="$PROJECT_ROOT/.env"
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
    cat << EOF
Usage: $0 [OPTIONS] TEMPLATE_FILE

Process XML template files with environment variables from .env

ARGUMENTS:
    TEMPLATE_FILE    Template file path relative to .claude/template/
                    (e.g., 'init.xml' for .claude/template/init.xml)

OPTIONS:
    -e, --env FILE      Use specific .env file (default: .env in project root)
    -t, --template-dir  Template directory (default: .claude/template)
    -v, --verbose       Show verbose output
    -h, --help         Show this help

EXAMPLES:
    $0 init.xml                          # Process .claude/template/init.xml
    $0 prompts/system.xml               # Process .claude/template/prompts/system.xml
    $0 -e .env.prod init.xml            # Use .env.prod instead of .env
    $0 -v init.xml                      # Verbose output

TEMPLATE FORMAT:
    Use \$VARIABLE_NAME or \${VARIABLE_NAME} in your XML templates.
    Variables will be replaced with values from the .env file in project root.

EOF
}

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1" >&2
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${YELLOW}🔍${NC} $1" >&2
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            # If relative path, make it relative to project root
            if [[ "$2" =~ ^[^/] ]]; then
                ENV_FILE="$PROJECT_ROOT/$2"
            else
                ENV_FILE="$2"
            fi
            shift 2
            ;;
        -t|--template-dir)
            # If relative path, make it relative to project root
            if [[ "$2" =~ ^[^/] ]]; then
                TEMPLATE_DIR="$PROJECT_ROOT/$2"
            else
                TEMPLATE_DIR="$2"
            fi
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            echo "Use -h or --help for usage information."
            exit 1
            ;;
        *)
            if [[ -z "$TEMPLATE_FILE" ]]; then
                TEMPLATE_FILE="$1"
            else
                log_error "Multiple template files specified. Only one is allowed."
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if template file argument was provided
if [[ -z "$TEMPLATE_FILE" ]]; then
    log_error "Template file not specified."
    echo "Use -h or --help for usage information."
    exit 1
fi

# Construct full template path
FULL_TEMPLATE_PATH="$TEMPLATE_DIR/$TEMPLATE_FILE"

log_verbose "Script location: $SCRIPT_DIR"
log_verbose "Project root: $PROJECT_ROOT"
log_verbose "Template directory: $TEMPLATE_DIR"
log_verbose "Template file: $TEMPLATE_FILE"
log_verbose "Full template path: $FULL_TEMPLATE_PATH"
log_verbose "Environment file: $ENV_FILE"

# Check if envsubst is available
if ! command -v envsubst &> /dev/null; then
    log_error "envsubst not found."
    echo "Install with:"
    echo "  macOS: brew install gettext"
    echo "  Ubuntu/Debian: apt-get install gettext-base"
    exit 1
fi

# Check if .env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    log_error "$ENV_FILE file not found!"
    echo "Create a .env file in your project root with your project variables:"
    echo "PROJECT_NAME=\"Your Project\""
    echo "TECH_STACK=\"Your Stack\""
    echo "CURRENT_STATUS=\"Your Status\""
    exit 1
fi

# Check if template file exists
if [[ ! -f "$FULL_TEMPLATE_PATH" ]]; then
    log_error "Template file '$FULL_TEMPLATE_PATH' not found!"

    # Show available templates if template directory exists
    if [[ -d "$TEMPLATE_DIR" ]]; then
        echo ""
        echo "Available templates in .claude/template/:"
        find "$TEMPLATE_DIR" -name "*.xml" -type f | sed "s|^$TEMPLATE_DIR/||" | sort
    fi
    exit 1
fi

log_verbose "Loading environment variables from $ENV_FILE..."

# Load environment variables and show them if verbose
if [[ "$VERBOSE" == "true" ]]; then
    log_verbose "Environment variables:"
    while IFS= read -r line; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        echo "  $line" >&2
    done < "$ENV_FILE"
fi

log_verbose "Processing template: $FULL_TEMPLATE_PATH"

# Process the template with environment variables
# Use set -a to export all variables, then source the .env file
(
    set -a  # Mark all variables for export
    # Source the .env file in a subshell to avoid polluting the current environment
    source "$ENV_FILE" 2>/dev/null || {
        # Fallback: parse manually if sourcing fails
        while IFS= read -r line; do
            # Skip empty lines and comments
            [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
            # Export the variable
            export "$line"
        done < <(grep -v '^[[:space:]]*#' "$ENV_FILE" | grep -v '^[[:space:]]*$')
    }
    envsubst < "$FULL_TEMPLATE_PATH"
)

# Log success to stderr so it doesn't interfere with output
log_success "Template processed successfully!" >&2
