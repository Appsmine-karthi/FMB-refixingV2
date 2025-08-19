#!/bin/bash

if [ -f ".env" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
else
  echo ".env file not found!"
  exit 1
fi

for dir in "$PDF_TEMP" "$INPUT_TEMP" "$OUTPUT_TEMP"; do
  if [ -n "$dir" ]; then
    mkdir -p "$dir"
    echo "Created: $dir"
  else
    echo "Warning: one of the variables is empty"
  fi
done
