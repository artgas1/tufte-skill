#!/bin/bash
# Copy the fixture chart into the empty workspace (runs only with --scaffold).
set -e
cp "$(dirname "$0")/../../dev2/fixtures/F5/chart.png" chart.png
