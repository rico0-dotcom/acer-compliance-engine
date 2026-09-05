# Local official-source ingestion

Place the official English consolidated EU AI Act source downloaded from EUR-Lex
into this directory as:

    eu_ai_act_source.html

Target consolidated version:

    CELEX 02024R1689-20260727
    Access/current version date: 27 July 2026

Source:
    https://eur-lex.europa.eu/eli/reg/2024/1689

The ingestion script does not fabricate regulatory text. It validates that the
local snapshot contains the regulation title and the required Articles 9, 10,
12, 13, 14, 15 and 50 before extracting them.

The script also records a SHA-256 hash of the exact local source snapshot.
