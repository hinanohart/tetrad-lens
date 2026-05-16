# Langfuse dashboard filters

These are the recommended filter expressions you can paste into the Langfuse "Scores" filter to surface the spans `tetrad-lens` is most useful for.

## Low-confidence LLM tags (needs human review)

```
attribute["tetrad.tier"] = "llm"
AND attribute["tetrad.confidence"] < 0.6
```

## High reverse-axis spans (second-order risk)

```
attribute["tetrad.reverse"] >= 0.5
```

These are the actions that, pushed to the limit, flip into something the user did not ask for. Read McLuhan & McLuhan, *Laws of Media* (1988), pp. 98–99 for the framework.

## Retrieve + Obsolesce simultaneously high (re-introducing an old pattern while killing a current one)

```
attribute["tetrad.retrieve"] >= 0.5
AND attribute["tetrad.obsolesce"] >= 0.5
```

## Annotation-corrected spans (human disagreed with the LLM)

The Langfuse v4 score API doesn't accept a `source=` kwarg, so `tetrad-lens` flags annotator-authored scores via a comment prefix and a metadata key (see `python/src/tetrad_lens/review_queue.py`). Filter on either:

```
score.name STARTSWITH "tetrad_v1."
AND score.comment STARTSWITH "[ANNOTATION:"
```

or, if you prefer the metadata path:

```
score.name STARTSWITH "tetrad_v1."
AND score.metadata["tetrad_lens.source"] = "ANNOTATION"
```
