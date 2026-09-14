#!/usr/bin/env bash
#
# targeted-crack.sh - Build a targeted wordlist plus a composite-affix rule set
# and crack with the rules integrated directly into the hashcat flow.
#
# One consolidated pipeline:
#   1. combiner -> compact base wordlist (per-component CamelCase + linguistic
#                  linking-word connectors)
#   2. affix    -> composite-affix hashcat rule set (core, special+core,
#                  core+special, special+core+special)
#   3. hashcat  -> applies the rule set on the GPU during cracking (-r), so the
#                  huge expansion never has to be written to disk.
#
# Use --expand to also materialize the fully expanded wordlist. Use --run with
# --hashfile and --hashmode to launch hashcat; otherwise the ready command is
# printed.
#
# Examples:
#   ./scripts/targeted-crack.sh --keywords alpha,bravo,charlie --dates '0724,1988'
#   ./scripts/targeted-crack.sh --keywords alpha,bravo --dates '0724' \
#       --hashfile hashes.txt --hashmode 1000 --run
#
set -euo pipefail

KEYWORDS=()
DATES=""
SPECIALS='!,@,#'
LINKLANG='pt'
CONNECTORS='EMPTY,_,.,na,no,da'
OUTDIR='generated'
HASHFILE=""
HASHMODE=""
EXPAND=0
RUN=0

usage() {
    echo "Usage: $0 --keywords a,b,c --dates '0724,1988' [--specials '!,@,#']" \
         "[--link-lang pt] [--connectors LIST] [--out DIR]" \
         "[--hashfile FILE --hashmode MODE] [--expand] [--run]"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --keywords)   IFS=',' read -ra KEYWORDS <<< "$2"; shift 2 ;;
        --dates)      DATES="$2"; shift 2 ;;
        --specials)   SPECIALS="$2"; shift 2 ;;
        --link-lang)  LINKLANG="$2"; shift 2 ;;
        --connectors) CONNECTORS="$2"; shift 2 ;;
        --out)        OUTDIR="$2"; shift 2 ;;
        --hashfile)   HASHFILE="$2"; shift 2 ;;
        --hashmode)   HASHMODE="$2"; shift 2 ;;
        --expand)     EXPAND=1; shift ;;
        --run)        RUN=1; shift ;;
        -h|--help)    usage; exit 0 ;;
        *)            echo "unknown argument: $1"; usage; exit 2 ;;
    esac
done

if [[ ${#KEYWORDS[@]} -eq 0 || -z "$DATES" ]]; then
    usage
    exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WLF="$ROOT/wlf.py"
[[ -f "$WLF" ]] || { echo "wlf.py not found at $WLF"; exit 1; }

mkdir -p "$OUTDIR"
BASES="$OUTDIR/targeted_bases.lst"
RULE="$OUTDIR/targeted_affix.rule"

echo "[1/3] combiner -> $BASES"
python "$WLF" combiner "${KEYWORDS[@]}" --titlecase --link-lang "$LINKLANG" \
    --assume-yes --connectors "$CONNECTORS" -o "$BASES"

echo "[2/3] affix rule set -> $RULE"
python "$WLF" affix "$BASES" --dates "$DATES" --specials "$SPECIALS" --emit-ruleset "$RULE"

if [[ $EXPAND -eq 1 ]]; then
    echo "[2b] affix expanded wordlist -> $OUTDIR/targeted_expanded.lst"
    python "$WLF" affix "$BASES" --dates "$DATES" --specials "$SPECIALS" \
        -o "$OUTDIR/targeted_expanded.lst"
fi

if [[ -n "$HASHFILE" && -n "$HASHMODE" ]]; then
    HC="hashcat -a 0 -m $HASHMODE $HASHFILE $BASES -r $RULE"
else
    HC="hashcat -a 0 -m <MODE> <HASHFILE> $BASES -r $RULE"
fi
echo "[3/3] cracking command (rules integrated):"
echo "  $HC"

if [[ $RUN -eq 1 ]]; then
    command -v hashcat >/dev/null 2>&1 || { echo "hashcat not found in PATH; skipping run."; exit 0; }
    if [[ -z "$HASHFILE" || -z "$HASHMODE" ]]; then
        echo "provide --hashfile and --hashmode to run hashcat."
        exit 0
    fi
    exec hashcat -a 0 -m "$HASHMODE" "$HASHFILE" "$BASES" -r "$RULE"
fi
