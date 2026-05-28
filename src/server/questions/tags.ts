export function normalizeTagNames(tagNames: string[]) {
  const seen = new Set<string>();
  const normalized: string[] = [];

  for (const rawName of tagNames) {
    const name = rawName.trim().replace(/\s+/g, " ");
    if (!name) continue;
    const key = name.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    normalized.push(name);
  }

  return normalized;
}
