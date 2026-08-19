# Clarity

Clarity is a desktop music player: it resolves songs from streaming providers, caches and downloads them, and plays them through a QML interface.

This glossary covers **background work** and the **domain/binding** separation — the terms settled while designing those two rewrites. Other areas (playback, caching, providers) are not yet described here; add them as they get resolved.

## Language

### Background work

**Runtime**:
The single process-wide object that owns the event loop, the thread pool, and the lanes. Started and stopped explicitly by the application.
_Avoid_: worker, bgworker, asyncBgworker, the background worker system

**Lane**:
A named execution context with its own concurrency rules, chosen by the caller to declare intent. There are exactly three: `io`, `blocking`, and `serial`.
_Avoid_: pool, executor, queue

**Job**:
One submission of one callable to a lane. A job is a single attempt, not a standing intention — submitting the same callable twice creates two jobs (unless they coalesce).
_Avoid_: task, work item, runnable

**Handle**:
The object returned by a submission, representing that job's outcome: its result, its failure, and the ability to cancel it. The only supported way to learn whether a job finished.
_Avoid_: future, promise, ticket

**Key**:
A caller-supplied string identifying *what a job is about* rather than which function it calls. Required on the serial lane. Keys are how two independent call sites recognise that they want the same work done.
_Avoid_: lock name, job id, tag

**Coalescing**:
Returning the existing handle when a job is submitted under a key that is already live, so every caller shares one execution and one result. Clarity's mutual-exclusion mechanism.
_Avoid_: deduplication, locking, debouncing

**Cooperative cancellation**:
Cancellation a job body opts into by accepting a token and checking it at points where its persistent state is safe. Distinct from cancelling a job that has not started, which needs no cooperation.
_Avoid_: soft cancel, graceful abort

**Resumable**:
A property of a job that touches persistent state: if it stops at any cancellation point, what it leaves behind is either untouched or a valid partial state a later attempt can continue from. Never a half-written state that claims to be complete.
_Avoid_: rollback, transactional, atomic

**Domain signal**:
A Qt signal owned by a domain object announcing something about *that object* — `songInfoFetched`, `playbackReadyChanged`. Bound by QML. Unrelated to the jobs that happen to cause them.
_Avoid_: callback, event, notification

**Job lifecycle event**:
Notification that *a specific submission* finished, failed, or was cancelled. Carried by a handle, never by a domain signal — a domain signal cannot say which submission it belongs to.
_Avoid_: completion signal, done event

### Domain and binding

**Song**:
A piece of music as the app understands it, identified across providers. Deliberately **not** a class — the code names the precise pieces below, because a class called `Song` accumulates everything.
_Avoid_: track, video, item

**Store**:
The in-memory holder of all runtime state for one kind of domain object, keyed by id, with subscription. Never touches disk and never blocks.
_Avoid_: cache, registry, repository, manager

**State**:
The mutable runtime facts about one domain object — what has been loaded, what is downloading, what is ready to play. A plain dataclass, distinct from the fetched facts it contains.
_Avoid_: model, record

**Operation**:
A function that performs domain work and writes the outcome into a store, owning the status transitions along the way. Distinct from a provider fetcher, which is pure and touches no store.
_Avoid_: task, service, action, command

**View model**:
The `QObject` adapter QML binds to: main-thread-only, one per id, cached, holding no domain logic of its own. The only place `QProperty` appears.
_Avoid_: proxy, wrapper, view, binding object

**Bridge**:
The single object that carries store changes from whichever thread produced them onto the main thread. The one place threads and Qt meet.
_Avoid_: dispatcher, marshaller, relay

**Pin**:
A claim that a store entry must not be evicted while something is depending on it — queued, downloading, or on screen.
_Avoid_: lock, hold, reference

**Rehydrate**:
Rebuilding an evicted store entry from the on-disk cache. Always off the main thread, always behind a placeholder.
_Avoid_: reload, restore, refetch
