#!/usr/bin/env bash
# Download full licence texts into data_package/licenses/ and write the MIT text.
# Run from publication/data_package/.
set -euo pipefail
mkdir -p licenses
curl -fsSL https://opendatacommons.org/licenses/odbl/odbl-10.txt -o licenses/ODbL-1.0.txt
curl -fsSL https://creativecommons.org/licenses/by/4.0/legalcode.txt -o licenses/CC-BY-4.0.txt
# MIT text is taken from LICENSE.md (between the ``` fences after "## MIT License")
awk '/^## MIT License/{f=1;next} f&&/^```/{c++; if(c==2)exit; next} f&&c==1' LICENSE.md > licenses/MIT.txt
for f in licenses/*.txt; do
  [ -s "$f" ] || { echo "Empty: $f" >&2; exit 1; }
  echo "OK  $f ($(wc -l < "$f") lines)"
done
