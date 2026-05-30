export const meta = {
  name: 'acmet-factcheck',
  description: 'Fact-check every Academic Metals Directory person + program: alive? still in the job? name changed? current links? what happened to the program? Each claim sourced + adversarially verified.',
  phases: [
    { title: 'Research people' },
    { title: 'Verify people' },
    { title: 'Research programs' },
    { title: 'Verify programs' },
  ],
}

const people = /*__PEOPLE__*/[]
const programs = /*__PROGRAMS__*/[]
log(`Fact-checking ${people.length} people and ${programs.length} programs.`)

function bornYear(dob) {
  const m = (dob || '').match(/(18|19|20)\d\d/)
  return m ? parseInt(m[0]) : null
}

const PERSON_SCHEMA = {
  type: 'object',
  required: ['slug', 'name', 'alive', 'name_changed', 'still_in_archived_job', 'confidence', 'sources'],
  properties: {
    slug: { type: 'string' },
    name: { type: 'string' },
    alive: { type: 'string', enum: ['yes', 'no', 'likely-deceased', 'unknown'] },
    death_info: { type: 'string', description: 'death year/obituary if deceased, else empty' },
    name_changed: { type: 'boolean' },
    current_name: { type: 'string', description: 'if changed, the current name; else empty' },
    still_in_archived_job: { type: 'string', enum: ['yes', 'no', 'retired-emeritus', 'unknown'] },
    current_role: { type: 'string', description: 'current/last known position + institution' },
    current_link: { type: 'string', description: 'best current canonical URL about them' },
    summary: { type: 'string', description: 'one or two sentence update' },
    sources: {
      type: 'array',
      items: { type: 'object', required: ['url'], properties: { url: { type: 'string' }, title: { type: 'string' } } },
    },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    notes: { type: 'string' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['confirmed', 'confidence'],
  properties: {
    confirmed: { type: 'boolean', description: 'do independent sources support the claim?' },
    correction: { type: 'string', description: 'corrected fact if the claim was wrong; else empty' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    note: { type: 'string' },
    extra_sources: { type: 'array', items: { type: 'string' } },
  },
}

const PROGRAM_SCHEMA = {
  type: 'object',
  required: ['slug', 'name', 'still_exists', 'confidence', 'sources'],
  properties: {
    slug: { type: 'string' },
    name: { type: 'string' },
    still_exists: { type: 'string', enum: ['yes', 'no', 'merged-renamed', 'unknown'] },
    current_name: { type: 'string' },
    current_status: { type: 'string', description: 'degrees offered now, dept it sits in' },
    current_chair: { type: 'string', description: 'current program head/chair if findable' },
    current_link: { type: 'string' },
    what_happened: { type: 'string', description: 'closure/merge/rename/continuation since ~2014' },
    sources: { type: 'array', items: { type: 'object', required: ['url'], properties: { url: { type: 'string' }, title: { type: 'string' } } } },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    notes: { type: 'string' },
  },
}

function personPrompt(p) {
  const edu = (p.education || []).map(e => `${e.level}: ${e.school} (${e.degree})`).join('; ')
  const by = bornYear(p.dob)
  const hist = by && by < 1930 ? '\nNOTE: born before 1930 — likely a historical figure; prioritize confirming death/legacy (obituary, museum memorial) over current employment.' : ''
  return `You are fact-checking ONE entry from an archived (offline since ~2014-2019) US academic directory of
metalsmiths/jewelers, the Tyler School of Art "Academic Metals Directory."

ARCHIVED RECORD:
  Name: ${p.name}
  Born: ${p.dob || 'unknown'}
  Archived as "currently teaching at": ${p.currently_at || 'n/a'}${p.since_year ? ' since ' + p.since_year : ''}
  Education: ${edu || 'n/a'}${hist}

This is a JEWELER / METALSMITH / METALS-ARTS EDUCATOR. Do NOT confuse them with a same-named person in
another field. Use WebSearch + WebFetch. Prioritize: the institution's own faculty page, the artist's own
site, Wikipedia, SNAG (snagmetalsmith.org), museum collections, obituaries.

Determine, with sources for each:
  - Are they still alive? (look for an obituary; only mark deceased if dates/obit support it)
  - Has their NAME CHANGED? (married name, professional rename) This is high-value — check carefully.
  - Are they still in the archived job, retired/emeritus, or moved? Current/last-known role + institution?
  - Best current canonical link about them.

Be honest about uncertainty (use 'unknown', confidence 'low'). NEVER invent a source URL. Return ONLY the structured object with slug="${p.slug}".`
}

function programPrompt(pg) {
  const fac = (pg.faculty || []).filter(Boolean).slice(0, 6).join(', ')
  return `You are fact-checking ONE US academic jewelry/metals/CAD-CAM PROGRAM from an archived (offline since
~2014-2019) directory.

ARCHIVED RECORD:
  Program/School: ${pg.name}
  Metals program started: ${pg.started || 'unknown'}
  Archived faculty: ${fac || 'n/a'}

Use WebSearch + WebFetch (institution site first, then news, accreditation, SNAG). Determine, with sources:
  - Does the metals/jewelry program still exist, or was it closed / merged / renamed?
  - Current degrees offered + which department it sits in now.
  - Current program head/chair if findable.
  - What happened since ~2014 (continuation, closure, leadership change).
  - Best current canonical link.

Be honest about uncertainty. NEVER invent a source URL. Return ONLY the structured object with slug="${pg.slug}".`
}

// --- people: research, then verify the high-impact / uncertain findings ----
const peopleResults = await pipeline(
  people,
  (p) => agent(personPrompt(p), { label: `research:${p.name}`, phase: 'Research people', schema: PERSON_SCHEMA, agentType: 'general-purpose' })
           .then(r => ({ ...r, slug: p.slug })).catch(() => null),
  async (finding, p) => {
    if (!finding) return null
    const by = bornYear(p.dob)
    const expectedDeceased = by && by < 1930 && (finding.alive === 'likely-deceased' || finding.alive === 'no')
    const risky = !expectedDeceased && (
      finding.name_changed || finding.alive === 'no' || finding.alive === 'likely-deceased'
      || finding.still_in_archived_job === 'no' || finding.confidence === 'low')
    if (!risky) return { ...finding, verified: 'not-needed' }
    const claim = `Person "${p.name}" (metalsmith/jeweler, b.${p.dob || '?'}): `
      + `alive=${finding.alive}; name_changed=${finding.name_changed}${finding.current_name ? ' ->' + finding.current_name : ''}; `
      + `job=${finding.still_in_archived_job}; current_role=${finding.current_role || ''}. `
      + `Cited sources: ${(finding.sources || []).map(s => s.url).join(' , ')}`
    const v = await agent(
      `Independently try to REFUTE or confirm this fact-check claim using your own WebSearch/WebFetch. `
      + `Be skeptical of same-name confusion. ${claim}\nReturn the verdict object.`,
      { label: `verify:${p.name}`, phase: 'Verify people', schema: VERDICT_SCHEMA, agentType: 'general-purpose' }
    ).catch(() => null)
    return { ...finding, verified: v ? (v.confirmed ? 'confirmed' : 'disputed') : 'verify-failed', verify: v }
  }
)

// --- programs: research, then verify closures/renames -----------------------
const programResults = await pipeline(
  programs,
  (pg) => agent(programPrompt(pg), { label: `research:${pg.name}`, phase: 'Research programs', schema: PROGRAM_SCHEMA, agentType: 'general-purpose' })
            .then(r => ({ ...r, slug: pg.slug })).catch(() => null),
  async (finding, pg) => {
    if (!finding) return null
    const risky = finding.still_exists !== 'yes' || finding.confidence === 'low'
    if (!risky) return { ...finding, verified: 'not-needed' }
    const v = await agent(
      `Independently confirm or refute: the metals/jewelry program at "${pg.name}" is currently `
      + `"${finding.still_exists}" (${finding.what_happened || ''}). Use WebSearch/WebFetch. Return the verdict object.`,
      { label: `verify:${pg.name}`, phase: 'Verify programs', schema: VERDICT_SCHEMA, agentType: 'general-purpose' }
    ).catch(() => null)
    return { ...finding, verified: v ? (v.confirmed ? 'confirmed' : 'disputed') : 'verify-failed', verify: v }
  }
)

const people_out = peopleResults.filter(Boolean)
const programs_out = programResults.filter(Boolean)
log(`Done: ${people_out.length} people, ${programs_out.length} programs fact-checked.`)
return { people: people_out, programs: programs_out }
