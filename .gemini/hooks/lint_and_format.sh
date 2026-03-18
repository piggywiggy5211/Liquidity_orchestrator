#!/usr/bin/env bash

# Read JSON from Gemini CLI
input=$(cat)

# In AfterAgent context there is no tool_input, so the variable will be empty.
# We just run checks on the entire project.
uv run ruff format . >&2
uv run ruff check --fix . >&2

# Run Mypy
mypy_output=$(uv run mypy . 2>&1)
mypy_status=$?

if [ $mypy_status -ne 0 ]; then
    # If Mypy fails, we deny the AI response and force it to fix the errors.
    # The reason will be sent back to the AI as a prompt.
    jq -n --arg out "$mypy_output" '{
      "decision": "deny",
      "reason": ("Mypy type check failed. Please fix these errors before finishing:\n\n" + $out),
      "systemMessage": "❌ Type check failed"
    }'
    exit 0
fi

# If everything is fine, allow the response
echo '{"decision": "allow"}'
exit 0
