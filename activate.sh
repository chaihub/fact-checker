#!/bin/bash
# Convenience script to activate virtual environment and set PYTHONPATH

export PYTHONPATH=/home/chai/chaihub/fact-checker/src:$PYTHONPATH
source /home/chai/chaihub/fact-checker/venv/bin/activate

echo "Virtual environment activated"
echo "Python: $(which python)"
echo "PYTHONPATH: $PYTHONPATH"
