#!/bin/bash

#take path as input or cwd if not provided
DIRECTORY="${1:-$(pwd)}"

#find all .tar files and extract them in place (in the same subdir)
find "$DIRECTORY" -type f -iname "*.tar*" -print0 | while IFS= read -r -d '' tarfile; do
  echo "Extracting: $tarfile"
  tar -xf "$tarfile" -C "$(dirname "$tarfile")"
  if [ $? -ne 0 ]; then
    echo "Error extracting $tarfile"
  fi
done

#use find to locate all .dicom.zip files and unzip them in place (in the same subdir)
find "$DIRECTORY" -type f -iname "*.zip" -print0 | while IFS= read -r -d '' zipfile; do
  echo "Unzipping: $zipfile"
  unzip -q "$zipfile" -d "$(dirname "$zipfile")"
  if [ $? -ne 0 ]; then
    echo "Error unzipping $zipfile"
  fi
done
