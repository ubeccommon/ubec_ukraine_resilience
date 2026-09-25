#!/usr/bin/env bash
# Repository rules; also run locally:  bash .github/workflows/guards.sh
set -u
fail=0

bad=$(git ls-files -ci --exclude-standard)
if [[ -n "$bad" ]]; then echo "FAIL tracked files match an ignore rule:"; echo "$bad"; fail=1; fi

big=$(git ls-files -z | xargs -0 du -k | awk '$1 > 5120 {print $2 " (" $1 " KB)"}')
if [[ -n "$big" ]]; then echo "FAIL files over 5 MB:"; echo "$big"; fail=1; fi

terms=$(git ls-files | grep -E '(^|/)dtm_[^/]*\.csv$|rescore_long\.csv$|oblast_context_k1\.csv$' || true)
if [[ -n "$terms" ]]; then echo "FAIL data whose terms forbid redistribution:"; echo "$terms"; fail=1; fi

while IFS= read -r -d '' f; do
  cols=$(head -1 "$f" | tr ',;' '\n\n' | grep -iE 'garrison|pdfo_mil|milit' | tr '\n' ' ' || true)
  if [[ -n "$cols" ]]; then echo "FAIL R4 columns in $f: $cols"; fail=1; fi
done < <(git ls-files -z '*.csv')

[[ $fail -eq 0 ]] && echo "guards: all passed"
exit $fail
