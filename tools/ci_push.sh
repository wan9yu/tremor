#!/bin/sh
# Commit the given paths and push, rebasing and retrying on a rejected push.
#
#   tools/ci_push.sh "<commit message>" <path> [<path>...]
#
# One home for the daily workflow's retry policy: the daily job shares its
# branch with the intraday sampler, and observed scheduler delays exceed the
# cron offset between them, so a bare push can be rejected at any time. Both
# daily commit steps call this; intraday.yml keeps its own deliberately
# DIFFERENT variant (pull before first push, exit 0 on final failure — losing
# a side-sample is acceptable, losing a day is not).
set -e
message="$1"
shift

git add "$@"
if git diff --cached --quiet; then
  echo "no changes to commit"
  exit 0
fi
git commit -m "$message"
for attempt in 1 2 3; do
  if git push; then
    exit 0
  fi
  echo "push attempt $attempt rejected"
  if [ "$attempt" = 3 ]; then
    break
  fi
  echo "rebasing and retrying"
  git pull --rebase --quiet origin main
  sleep 5
done
echo "could not push after 3 attempts"
exit 1
