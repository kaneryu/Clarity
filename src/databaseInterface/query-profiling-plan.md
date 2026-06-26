# Query Profiling Plan

## Goal

Add lightweight query profiling to the database layer so Clarity can identify:

- the most frequently executed repository queries
- the queries with the highest total runtime
- the slowest individual queries
- query shapes that should drive future index changes

This should be implemented without scattering instrumentation across every repository method.

## Guiding Approach

Instrumentation should live in the shared database execution path, not in each repository.

Repositories should provide stable query names where practical, but the actual timing, aggregation, and logging should happen in one central place.

## Scope

### In scope

- measure execution time for SQL statements issued through the shared database layer
- aggregate stats in memory by stable query name
- optionally store normalized SQL text alongside the query name for debugging
- record success or failure counts
- record row counts where cheap and reliable
- expose a way to dump the hottest queries for debugging
- optionally support a slow-query threshold for warning logs

### Out of scope for the first pass

- persistent storage of query metrics
- logging every raw query to disk in normal operation
- automatic EXPLAIN QUERY PLAN for every query
- percentile tracking beyond simple max or average
- instrumentation bolted directly into repository business logic

## Suggested Architecture

### 1. Add a central profiling data structure

Create a small profiler object or module near the database core layer.

Suggested tracked fields per query key:

- query_name
- normalized_sql
- execution_count
- total_duration_ms
- max_duration_ms
- slow_count
- error_count
- last_error
- last_duration_ms
- last_seen_at

If row counts are available cheaply, also track:

- total_rows_returned
- last_row_count

### 2. Instrument the shared execution helpers

Identify the narrowest common execution boundary in the database layer, likely in [dbcore.py](dbcore.py) or the shared repository base utilities.

Wrap the execution path with:

- start timestamp
- execute SQL
- collect success or failure
- compute duration
- update aggregated metrics

Do this for the common query shapes:

- execute with no returned rows
- fetch one
- fetch many
- executemany if used

### 3. Use stable query names

Each repository query should provide a stable name such as:

- song_repository.get_by_id
- listen_event_repository.get_recent_for_song
- playlist_repository.add_song

Do not key metrics only by fully rendered SQL with parameters substituted. That is too noisy and fragments the profile.

If a query name is not provided, fall back to normalized SQL text.

### 4. Normalize SQL for debugging

Store the SQL template text without interpolated values.

Avoid logging full parameter payloads by default. If parameter logging is ever added, it should be:

- opt-in
- redacted where needed
- summarized instead of dumped verbatim

### 5. Add a debug dump surface

Provide a simple way to inspect current metrics, for example:

- a function returning the top queries by total duration
- a function returning the top queries by execution count
- a function returning the slowest max-duration queries

Possible output formats:

- list of dicts for programmatic consumption
- formatted debug log table
- optional developer-only command or debug page later

### 6. Add slow-query logging

Add a configurable threshold, for example 10 ms, 25 ms, or 50 ms.

If a query exceeds the threshold:

- increment slow_count
- optionally emit a warning log with query name and duration

Keep this conservative to avoid log spam.

## SQLite-Specific Follow-up Workflow

The profiler should identify candidate queries. It should not try to solve query planning automatically.

Once hot queries are known:

1. run EXPLAIN QUERY PLAN manually on the top offenders
2. verify whether SQLite is scanning or using an index
3. add or adjust indexes based on actual query shapes
4. re-test and compare the profile

## Implementation Steps

1. Inspect the shared database execution path in [dbcore.py](dbcore.py) and any repository base helpers.
2. Add a lightweight in-memory profiler class or module under databaseInterface.
3. Instrument the common execute and fetch helpers.
4. Add support for explicit query names.
5. Add a debug dump method returning sorted aggregated metrics.
6. Add optional slow-query warning logs.
7. Run common app flows and collect a first real profile.
8. Use the profile to revisit indexes in [schema.sql](schema.sql).

## Suggested API Shape

This does not need to be exact, but something close to this would keep the design clean:

```python
db.fetch_one(
    sql,
    params,
    query_name="song_repository.get_by_id",
)

db.fetch_all(
    sql,
    params,
    query_name="listen_event_repository.get_recent_for_song",
)

db.execute(
    sql,
    params,
    query_name="playlist_repository.add_song",
)
```

And a profiler surface like:

```python
get_query_profile_summary(sort_by="total_duration_ms", limit=20)
reset_query_profile()
```

## Validation Checklist

- repeated executions of the same repository method aggregate into one metric entry
- parameter changes do not fragment the metrics
- errors increment error counters without breaking normal exception flow
- slow queries are visible in logs or summary output
- normal app usage does not produce excessive logging noise
- instrumentation overhead remains low

## Success Criteria

This work is complete when:

- Clarity can show the most common queries by count
- Clarity can show the most expensive queries by total runtime
- Clarity can identify worst-case slow queries
- future index work can be driven by real usage instead of guesses

## Notes

- Prefer keeping this entirely behind the database layer boundary.
- Do not spread timing code across repository business methods unless there is no common execution path.
- If needed later, a second phase can add EXPLAIN QUERY PLAN helpers for the top slow queries only.