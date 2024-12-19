#!/bin/bash

#takes path as input. uses cwd if not provided
DIRECTORY="${1:-$(pwd)}"

#use find to locate all .zip files and unzip them in place (in the same directory)
find "$DIRECTORY" -type f -iname "*.zip" | while read -r zipfile; do
  unzip -o "$zipfile" -d "$(dirname "$zipfile")"
done
