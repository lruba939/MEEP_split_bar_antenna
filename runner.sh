#!/bin/bash

# ============================================
# CONFIGURATION
# ============================================
NPROC=1

EXPERIMENT="bowtie_substrate"
SUBSTRATE="Au"
COMMENT="Test of trl for smaller dets."
EMPTY_CACHE="results/bowtie__lam-660__gap-6__L-87__T-30__R-5__ant-Au__sub-Au__19/cache/empty/"
SUBSTRATE_CACHE="results/bowtie__lam-660__gap-6__L-87__T-30__R-5__ant-Au__sub-Au__19/cache/substrate/"
ANTENNA_CACHE="results/bowtie__lam-660__gap-6__L-87__T-30__R-5__ant-Au__sub-Au__19/cache/antenna/"

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
    --substrate_cache="$SUBSTRATE_CACHE" \
    --antenna_cache="$ANTENNA_CACHE" \
    --empty_cache="$EMPTY_CACHE" \
    1> "$OUTFILE" \
    2> "$ERRFILE"

EXIT_CODE=$?

echo "======================================="
echo "Finished with exit code: $EXIT_CODE"
echo "stdout -> $OUTFILE"
echo "stderr -> $ERRFILE"
echo "======================================="

exit $EXIT_CODE
