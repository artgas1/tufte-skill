#!/bin/bash
# Copy the fixture chart into the empty workspace (runs only with --scaffold).
set -e
cp "$(dirname "$0")/../../dev/fixtures/F2/chart.png" chart.png
