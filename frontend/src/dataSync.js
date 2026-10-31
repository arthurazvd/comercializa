/** Utilities for reliable, non-blocking synchronization of API resources. */
export function upsertById(items, item) {
  if (!item || item.id == null) return items
  const index = items.findIndex(existing => existing.id === item.id)
  if (index === -1) return [item, ...items]
  return items.map((existing, position) => position === index ? item : existing)
}

export function removeById(items, id) {
  return items.filter(item => item.id !== id)
}

/** Ignore stale GET responses when a write or newer GET has already happened. */
export function createLatestLoader(fetchData, applyData) {
  const revisions = new Map()
  function invalidate(name) {
    revisions.set(name, (revisions.get(name) || 0) + 1)
  }
  async function load(name) {
    invalidate(name)
    const revision = revisions.get(name)
    const data = await fetchData(name)
    if (revisions.get(name) === revision) applyData(name, data)
    return data
  }
  return { load, invalidate }
}
