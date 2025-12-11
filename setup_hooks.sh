#!/bin/bash

echo "Installing Git Pre-commit Hook..."

# Write the hook directly to the .git directory
cat << 'EOF' > .git/hooks/pre-commit
#!/bin/sh
FORBIDDEN_PATTERNS="backups/|secrets/|\.env$|\.sql$|\.sql\.gz$"
STAGED_FILES=$(git diff --cached --name-only)

if echo "$STAGED_FILES" | grep -E -q "$FORBIDDEN_PATTERNS"; then
    echo "❌ COMMIT REJECTED: Sensitive files detected!"
    echo "$STAGED_FILES" | grep -E "$FORBIDDEN_PATTERNS"
    exit 1
fi
exit 0
EOF

# Make it executable
chmod +x .git/hooks/pre-commit

echo "✅ Hook installed successfully! You are now protected from committing secrets."