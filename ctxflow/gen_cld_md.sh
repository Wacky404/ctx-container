#!/bin/bash

set -e

if ! command -v envsubst &> /dev/null; then
    echo "envsubst not found."
    echo "Install with:"
    echo "  macOS: brew install gettext"
    echo "  Ubuntu/Debian: apt-get install gettext-base"
    exit 1
fi

if [[ ! -f .env.dev ]]; then
    echo ".env file not found!"
    echo "Create a .env file with your project variables:"
    echo "PROJECT_NAME=\"Your Project\""
    echo "TECH_STACK=\"Your Stack\""
    echo "CURRENT_STATUS=\"Your Status\""
    echo "PRIORITY=\"Your Priority\""
    exit 1
fi

# Check if template exists
if [[ ! -f ${pwd}/prompts/template_claudemd.xml ]]; then
    echo "Template file .claude/prompt_template.xml not found!"
    exit 1
fi

echo "Loading environment variables from .env..."

source .env

echo "Generating CLAUDE.md..."

# Generate the final CLAUDE.md file
envsubst < .claude/prompt_template.xml > CLAUDE.md

echo "CLAUDE.md generated successfully!"
