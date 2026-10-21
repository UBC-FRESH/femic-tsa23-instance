# Cost-effectiveness of hazard treatments, and how safe the ranking is

## The claim

On the TSA23 landscape, a fuel break buys hazard reduction far more cheaply than thinning,
and the ordering does not depend on the exact hazard values assumed.

## The arithmetic

Cost per hazard-hectare is area-independent, because both cost and hazard reduction scale
with area:

| intervention | hazard after | reduction per ha | cost per ha | cost per hazard-ha |
| --- | ---: | ---: | ---: | ---: |
| fuel break (FB) | 0.05 | 0.95 | $5,000 | **$5,263** |
| thinning then surface fuel (FT+SF) | 0.2 | 0.80 | $23,000 | $28,750 |
| thinning (FT) | 0.4 | 0.60 | $20,000 | $33,333 |

Two things follow.

1. **Surface fuel cannot be costed on its own.** Its source track is the FT destination, so
   it only follows a thinning. The E17 figure of $3,750 per hazard-hectare assumed a
   standalone SF treatment that the model cannot express. The true sequence costs $28,750.
2. **Thinning is not a hazard tool at these prices.** It costs about 6x a fuel break per
   hazard-hectare, and its surface-fuel follow-up does not fix that.

## How wrong would the numbers have to be?

Set the fuel-break hazard to `h`. A fuel break stops being the cheapest option when

```
5,000 / (1 - h)  >  20,000 / 0.6      =>      h > 0.85
```

So **a fuel break would have to cut hazard by less than 15% before thinning wins on cost per
hazard-hectare.** Against FT+SF the threshold is `h > 0.826`.

That is a bound, not a point estimate: it holds for any hazard value in the plausible range,
which means the conclusion does not rest on defending 0.05.

## Empirical check

`complete_hazard_feature.py --fb-hazard H` rebuilds the hazard curves; the greedy scheduler
then re-ranks every treatment.

| FB hazard | greedy selection | reduction |
| ---: | --- | ---: |
| 0.05 (default) | 2,969 fuel breaks | 20,856 hazard-ha |
| 0.20 | 2,891 fuel breaks | 17,856 hazard-ha |
| 0.80 | fuel breaks first, then thinning once the FB candidates run out | 9,484 hazard-ha |
| 0.90 | thinning only (479 blocks) | 9,298 hazard-ha |

At 0.8 the fuel break is still cheaper per unit ($25,000 against $33,333), so the mix
appears only because there are not enough FB candidates to spend the whole budget. At 0.9
the fuel break is dearer ($50,000), and the ranking flips — exactly where the algebra puts
it.

## What this means for the thesis

- The treatment ranking is **robust to the hazard assumption** over a range far wider than
  the uncertainty in the literature.
- The interesting sensitivity is **not** the hazard value but the **budget**: at $5,350 per
  hazard-hectare, a 2.25% landscape reduction needs about $118M, and $100M buys 1.9%.
- If the thesis wants thinning to be justified, it has to be justified on timber or
  silvicultural grounds, not on hazard reduction per dollar.

## Caveats

- Hazard reduction is read at year 4 of a 5-year horizon. A longer horizon would let the FB
  effect decay (8 years to baseline) and would favour longer-lived treatments.
- The greedy ranks per block and ignores spatial arrangement. E15/E16 show arrangement
  matters for area burned but not for the hazard account, which is a sum over hectares.
- Cost figures are the instance's assumptions ($20k/ha FT, $5k/ha FB, $3k/ha SF), not
  quotes.
