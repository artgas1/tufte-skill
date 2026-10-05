#!/bin/bash
# Copy the fixture chart into the empty workspace (runs only with --scaffold).
set -e
cp "$(dirname "$0")/../../dev3/fixtures/F7/chart.png" chart.png
