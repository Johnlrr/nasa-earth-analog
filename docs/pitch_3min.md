# SIMILITUDE: 3-minute pitch (English, about 420 words)

Numbers come from the submitted tables (`docs/slide_numbers.json`). The one result obtained after
the deadline is marked; say so out loud if you use it.

## 0:00–0:30 · The problem (slide 1–2)
"Space agencies rehearse Moon and Mars hardware at famous analog sites. We asked a test
engineer's question: which test results actually transfer? On the Moon Base ridge, Connecting
Ridge, 76 % of the terrain is steeper than 8°. At six classic analog sites the median is 9 %.
Famous is not faithful."

## 0:30–1:10 · How it works (slide 3)
"One formula on both worlds. NASA LOLA elevation on the Moon, a CTX elevation model on Mars,
Copernicus on Earth: the same slope, roughness, shadow and route-planner code on each side,
judged against 1,000 random bare-land cells. Every test variable gets a verdict: it transfers to
a field site, it needs a named facility, or orbit cannot tell."

## 1:10–1:50 · We tested ourselves (slide 4)
"We registered our tests before running them, and we publish the failures. Our mineral test
failed its own stop rule, so we publish no mineral site. Our traverse test failed with 8 lunar
neighbours; with 124 it passes against random land, narrowly, and it does not beat classic
sites. We say that on every card. On Mars, classic Mars analogs match Perseverance's Jezero
delta front 42 % of the time, random land 19 %."

*(after the deadline, optional)* "Since then we checked our slope against the rover itself: at 708
places where Perseverance stopped, our 30 m slope from orbit tracks the tilt the rover measured,
ρ = 0.80. Our route planner did not predict where the rover detoured, and we publish that too."

## 1:50–2:30 · What we found (slide 5–6)
"Two sites in countries open to NASA, outside known analog areas, pass both terrain tests on two
elevation models: one in Argentina, the only random cell of 1,000 that passed, and one on Baffin
Island, where for 71 days every daylight minute has the Sun below 7°, the polar low Sun no Earth
site has over a year. The slope match holds at 5 m with ArcticDEM."

## 2:30–3:00 · Why it matters (slide 7)
"A test team does not need one perfect site. It needs a campaign. Our two leads together cover
all five field rows that orbit can judge; the best classic site covers one. Eight rows go to
named facilities: gravity offload, thermal vacuum, dust. That maps to NASA's shortfalls in
surface mobility and precision landing. Next: a campaign card for each Artemis III candidate
region, so whichever region NASA picks, the Earth test plan is ready."

## Likely questions
- *Is 30 m enough?* No for rocks: they are UNOBSERVED on every card. Slope at 5 m checked for
  Baffin; the orbital slope matches rover tilt on Mars (after the deadline).
- *p = 0.049 is borderline.* Yes. With both registered looks it is 0.098; we do not call it
  confirmed, and the cards report slope and routes separately.
- *Why not Atacama or Devon?* They are in the comparison. Haughton fails the ridge's slope test and
  reproduces its routes in only 4 of 9 footprints; it covers 1 of 5 field rows.
- *Who would use this?* Analog campaign planners. It assigns no TRL; it feeds a project's
  "documented definition of relevant environment".
