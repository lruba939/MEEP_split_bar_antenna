#!/bin/bash

# ============================================
# CONFIGURATION
# ============================================
NPROC=2

EXPERIMENT="bowtie_substrate"
SUBSTRATE="Au"
COMMENT="Testing new source position"

LOG_OUTPUT="output"
LOG_ERROR="error"

# ============================================
# RUN
# ============================================
OUTFILE="${LOG_OUTPUT}.out"
ERRFILE="${LOG_ERROR}.err"

echo "======================================="
echo "Starting simulation"
echo "Experiment : $EXPERIMENT"
echo "Substrate  : $SUBSTRATE"
echo "Processes  : $NPROC"
echo "Output     : $OUTFILE"
echo "Errors     : $ERRFILE"
echo "======================================="

mpirun -np "$NPROC" \
    python main/run.py \
    --experiment="$EXPERIMENT" \
    --substrate="$SUBSTRATE" \
    --comment="$COMMENT" \
    1> "$OUTFILE" \
    2> "$ERRFILE"

EXIT_CODE=$?

echo "======================================="
echo "Finished with exit code: $EXIT_CODE"
echo "stdout -> $OUTFILE"
echo "stderr -> $ERRFILE"
echo "======================================="

exit $EXIT_CODE
