# v8.5.0 Research Timeline & Run History Map

```text
v8.1 environment revisions/checkpoints/recovery ─┐
v8.2 project activity/revisions                 ├─> v8.5 derived timeline
v8.3 asset revisions/provenance                 ┤       ├─ chronological events
v8.4 execution jobs/lifecycle/results           ┘       ├─ run history
                                                         ├─ lineage graph
                                                         ├─ neutral comparison
                                                         └─ Core event-binding plan
```

## Authority model
- v8.1 owns environment history.
- v8.2 owns project workspace activity.
- v8.3 owns asset revision history.
- v8.4 owns execution job history.
- v8.5 owns no competing copies of those histories; it derives integrity-checked events on request.

## Timestamp provenance
Recorded timestamps are preserved. Historical asset revisions created before v8.5 may not contain a timestamp; those events are marked `timeSource=unavailable-in-v8.3-record` and are not assigned an invented filesystem-derived chronology.
