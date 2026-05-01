#!/bin/bash
# Nightly jobs script for PiGenus
# This script is called by the pigenus-scheduler service

set -e

# Change to the PiGenus directory
cd /home/pi/pigenus

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run the nightly jobs
python -c "from core.scheduler import nightly_jobs; nightly_jobs()"

echo "Nightly jobs completed at $(date)"
