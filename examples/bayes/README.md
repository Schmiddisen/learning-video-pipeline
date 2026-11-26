# Example course: Bayes in Practice

A three-video demo course built with this pipeline – original content, English narration.

- `videos/v01_1/test_that_lies.py` – why a positive result from a 99 % test can mean 9 %
  (counting a thousand people)
- `videos/v01_2/odds.py` – Bayes' theorem as one multiplication of odds; why a second test
  moves 9 % to 91 %
- `videos/v01_3/courtroom.py` – the prosecutor's fallacy: a one-in-a-million match is not a
  one-in-a-million chance of innocence
- `cards/01_bayes.yaml` – flashcards, linked to the videos by `tags: [v1.1]`
- `labs/01_bayes.yaml` – a Python lab (simulate a population) and two step-by-step labs; the
  player designs further labs per section on demand
- `learner.md` – the learner profile every skill and the player's tutor read
- `voice_cache/` – the recorded narration, so rendering costs nothing

Render and open the study player:

```bash
uv sync
uv run lvp-build videos/v01_1/test_that_lies.py -q l --fps 15
uv run lvp-build videos/v01_2/odds.py -q l --fps 15
uv run lvp-player --clean     # → build/player/, publish it with the `player` skill
```
