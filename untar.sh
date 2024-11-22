#!/bin/bash

#take path as input or uses cwd if not provided
DIRECTORY="${1:-.}"

#find all .tar files and extract them in place (in same directory)
find "$DIRECTORY" -type f -iname "*.tar*" -print0 | while IFS= read -r -d '' tarfile; do
  echo "Extracting: $tarfile"
  tar -xf "$tarfile" -C "$(dirname "$tarfile")"
  if [ $? -ne 0 ]; then
    echo "Error extracting $tarfile"
  fi
done
