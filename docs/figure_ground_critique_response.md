# On the "Tetrad without Figure/Ground" critique

McLuhan scholars sometimes point out that lifting the four laws of media out of *Laws of Media* (McLuhan & McLuhan, University of Toronto Press, 1988) without their figure/ground partner concept loses much of what makes the framework McLuhan's. This is a fair critique. Here is how `tetrad-lens` handles it.

## What we kept

- The four laws as **orthogonal axes**, each with its own [0, 1] score and free-text rationale (`tetrad.{enhance, obsolesce, retrieve, reverse}`).
- The original phrasing of the four questions, in English and Japanese, in `schema/i18n/`.

## What we did not collapse

We did **not** collapse the four laws into a single "tetrad" enum. McLuhan & McLuhan (1988) are explicit that the four laws operate simultaneously on the same artifact; collapsing them would erase that. So a single span can read high on Enhance and Reverse at the same time, which is the typical case for any technology pushed to a useful scale.

## How figure/ground enters

`tetrad.figure_ground` is exposed in the schema but is **DERIVED, read-only**. Producers cannot set it. Consumers (dashboards, this SDK's `figure_ground_of(...)` helper) compute it from the four scores. The default rule is intentionally simple:

- **figure**  — `(enhance + retrieve) / 2 >= high` and the ground pair below `high`
- **ground**  — `(obsolesce + reverse) / 2 >= high` and the figure pair below `high`
- **both**    — both pairs above `high`
- **unclear** — all four scores below `low`

The thresholds (`high=0.6`, `low=0.2` by default) are tunable. The point is to make figure/ground a *visualization choice* on top of the four-axis data, not a separate piece of producer state that could disagree with the axes.

## What we did not implement (v0.1)

- Hot/cold media classification (Understanding Media, 1964, ch. 1–2)
- Acoustic space (Through the Vanishing Point, 1968)
- The figure/ground reversal table McLuhan would draw with Eric McLuhan when working through actual artifacts

These are on the v0.2+ roadmap (`docs/roadmap.md`).

## What "Tetrad" means in this project

A four-element observational lens with reserved attribute keys. We use lowercase "tetrad" throughout the codebase and docs. We do not claim the word — McLuhan's estate manages McLuhan's legacy; this project sits in the same fair-use space as academic, journalistic, and open-source uses of the framework. See CITATION.cff for the proper bibliographic credit.
