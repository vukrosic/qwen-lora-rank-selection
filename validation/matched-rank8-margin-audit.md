# Matched rank-8 margin audit

Status: **PASS**  
Classification: `TRANSFER_SUPPORTED`  
Portable classification SHA-256:
`f476d4eed5a7cc9d71c79f7342b2675a5fcd0d3fce616a2805c70be3ff793129`  
Source classification SHA-256:
`09c55c41866f19772ee37ce20e8952d1e7de0a93606c88a9b9df28d038aa698f`

This is a descriptive recomputation of the frozen exact-match and NLL gates,
not a significance test or confidence interval. Each seed has 96 test records;
means pool three seed-level rates on the corresponding 288-record grid.

## Seed-level selected-versus-other margins

| Seed | Selected | Selected exact | Other exact | Exact margin | Other minus selected NLL |
| ---: | --- | ---: | ---: | ---: | ---: |
| 20260841 | token | 95/96 | 37/96 | +58 records (+60.42 pp) | +0.3674828210 |
| 20260842 | token | 74/96 | 67/96 | +7 records (+7.29 pp) | +0.0241954118 |
| 20260843 | example | 55/96 | 10/96 | +45 records (+46.88 pp) | +0.4405646545 |

The selected arm has strictly lower NLL and no exact-match deficit on every
seed. The narrowest seed-level advantage is seed 20260842: seven exact records
and 0.0241954118 NLL.

## Aggregate selected-versus-fixed-policy margins

| Baseline | Mean exact margin | Worst exact margin | Mean NLL advantage | Worst NLL advantage |
| --- | ---: | ---: | ---: | ---: |
| Always token | +45/288 records (+15.63 pp) | +45/96 records (+46.88 pp) | +0.1468548848 | +0.4405646545 |
| Always example | +65/288 records (+22.57 pp) | +18/96 records (+18.75 pp) | +0.1305594109 | +0.1474030418 |

All strict aggregate comparisons are positive. The anti-floor condition also
passes: every selected arm has both short and long exact match above 5%.

