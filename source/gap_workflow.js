export const meta = {
  name: 'acmet-gap-analysis',
  description: 'Find notable US academic jewelry/metals programs MISSING from the archived directory, and programs created after it went offline (~2014).',
  phases: [{ title: 'Find gaps' }],
}

const archived = ["Abilene Christian University", "Academy of Art College", "Adams State College", "Appalachian Center for Crafts, T.T.U.", "Arizona State University", "Ball State University", "Barton County Community College", "Beaver College", "Birmingham Bloomfield Art Association", "Blue Mountain Community College", "Bowling Green State University", "Bradley University", "Cabrillo College", "California College of Arts and Crafts", "California State University - Fullerton", "California State University at Long Beach", "California State University, Northridge", "Calvin College", "Carnegie-Mellon University", "Casper College", "Center for Creative Studies", "Central Washington University", "Cheltenham Center for the Arts", "Clark College", "Cleveland Institute of Art", "College of DuPage", "College of the Redwoods", "Colorado State University", "Columbia College", "Columbus College", "Cranbrook Academy of Art", "Dakota State University", "Dallas Jewelry Institute", "Dunconnor Workshop", "East Carolina University", "East Tennessee State University", "East Texas Baptist University", "Eastern Illinois University", "Eastern Kentucky University", "Eastern Michigan University", "Eastern New Mexico University", "Eastfield College", "Edinboro University of Pennsylvania", "Emporia State University", "Fashion Institute of Technology", "Flagler College", "Florida Atlantic University", "Florida Gulf Coast Art Center", "Florida Keys Community College", "Georgia State University", "Georgian Court College", "Glassboro State College", "Glassell School of Art / The Museum of Fine Arts", "Harding University", "Hartnell College", "Haywood Community College", "Holland School for Jewelers", "Humboldt State University", "Idaho State University", "Illinois Central College", "Indiana Purdue University at Fort Wayne", "Indiana University", "Indiana University of Pennsylvania", "Institute of American Indian Arts", "Interlochen Center for the Visual Arts", "Iowa State University", "James Madison University", "Joliet Junior College", "Kansas State University", "Kendall College of Art and Design", "Kent State University", "Kutztown University of Pennsylvania", "Lane Community College", "Long Beach City College", "Long Island University", "Longwood College", "Maine College of Art", "Maryland Art Institute, Jewelry Institute", "Massachusetts College of Art", "Memphis College of Art", "Metairie Park Country Day School", "Miami Jewelry Institute", "Miami University", "Middle Tennessee State University", "Midwestern State University", "Millersville University", "Milwaukee Area Technical College", "Milwaukee Area Technical College/ South", "Milwaukee Area Technical College/North", "Minneapolis Technical College", "Missouri Southern State College", "Montana State University", "Montgomery College", "Mott Community College", "Nazareth College", "Nebraska Wesl e yan University", "New Jersey City University", "New Mexico State University", "New York University", "North Bennet Street School", "North Hennepin Community College", "Northeastern Illinois University", "Northern Arizona University", "Northern Illinois University", "Northern Michigan University", "Northwest Missouri State University", "Ohio State University", "Oklahoma State University", "Old Dominion University", "Oral Roberts University", "Oregon School of Arts & Crafts", "Palomar College", "Parsons School of Design", "Pasadena City College", "Pennsylvania State University", "Pittsburg State University", "Portland School of Art", "Purdue University", "Quincy College", "Revere Academy of Jewelry Arts", "Rhode Island College", "Rhode Island School of Design", "Roberts Wesleyan College", "Rochester Institute of Technology", "Rowan University", "San Antonio College", "San Diego State University", "San Francisco State University", "Savannah College of Art and Design", "Sawtooth Center for Visual Art", "School of the Museum of Fine Arts", "Seton Hill College", "Shorter College", "Siena Heights University", "Skidmore College", "Slippery Rock University", "Southeastern Louisiana University", "Southern Connecticut State University", "Southern Illinois University", "Southern Illinois University Carbondale", "Southwest Missouri State University", "Southwest School of Art and Craft", "Southwest Texas State University", "Spokane Falls Community College", "St. Norbert College", "State University College at Buffalo", "State University of New York at Brockport", "State University of New York at Geneseo", "State University of New York at New Paltz", "Stephen F. Austin State University", "Studio Jewelers, Ltd.", "Syracuse University", "Tarrant County Junior College/ N.E.", "Texas Tech University", "Texas Women's University", "The Florida State University", "The School of the Art Institute of Chicago", "The University of Akron", "The University of Mary Hardin-Baylor", "The University of Michigan", "The University of Texas Pan American", "The University of Texas at Austin", "The University of Texas at El Paso", "The University of Wisconsin -Milwaukee", "The University of the Arts", "Towson University", "Tufts University", "Tulsa Community College/Cultural & Social Services Division", "Tyler School of Art/Temple University", "University of Arizona", "University of Delaware", "University of Houston", "University of Illinois at Urbana-Champaign", "University of Iowa", "University of Kansas", "University of Massachusetts / Dartmouth", "University of Minnesota", "University of Missouri", "University of North Dakota", "University of North Texas", "University of Oregon", "University of Science & Arts of Oklahoma", "University of South Carolina", "University of Texas at Arlington", "University of Washington", "University of Wisconsin - Green Bay", "University of Wisconsin-Eau Claire", "University of Wisconsin-La Crosse", "University of Wisconsin-Madison", "University of Wisconsin-Stout", "University of Wisconsin-Whitewater", "Virginia Commonwealth University", "Washington University", "Wayne State University", "Weber State University", "Western Maryland College", "Western Montana College", "Western State College of Colorado", "Wichita Center for the Arts", "Winthrop College", "Yakima Valley Community College", "Yavapai College"]
log(`Gap analysis against ${archived.length} archived programs.`)

const LIST_SCHEMA = {
  type: 'object', required: ['programs'],
  properties: { programs: { type: 'array', items: {
    type: 'object', required: ['institution', 'note'],
    properties: {
      institution: { type: 'string' },
      program_name: { type: 'string' },
      degree_levels: { type: 'string' },
      founded_after_2014: { type: 'string', enum: ['yes','no','unknown'] },
      status: { type: 'string', enum: ['active','closed','unknown'] },
      note: { type: 'string' },
      source_url: { type: 'string' },
    } } } },
}

const archivedBlock = archived.join('; ')
const lenses = [
  { key: 'major-mfa', prompt: 'List notable CURRENT US graduate (MFA) and major BFA programs in JEWELRY / METALS / METALSMITHING active today (e.g. SUNY New Paltz, Cranbrook, RISD, SAIC, Tyler/Temple, U Washington, San Diego State, ECU, MassArt, Indiana University).' },
  { key: 'new-since-2014', prompt: 'List US academic JEWELRY / METALS programs, concentrations, endowed programs, or dedicated facilities FOUNDED, launched, renamed, or substantially established AFTER about 2014 (after this directory went offline).' },
  { key: 'craft-regional', prompt: 'List active US academic JEWELRY / METALS programs at art & craft colleges, community colleges, and regional state universities (the less-famous tier) that exist today.' },
  { key: 'closures', prompt: 'List notable US academic JEWELRY / METALS programs CLOSED, merged, or discontinued in roughly the last 10-15 years. Give institution + what happened.' },
]

const found = await parallel(lenses.map(l => () =>
  agent(
    'You are doing a GAP ANALYSIS for an archived US academic metals/jewelry directory. Use WebSearch + WebFetch.\n\n' + l.prompt +
    '\n\nIMPORTANT: EXCLUDE institutions already in our directory (do NOT list these): ' + archivedBlock +
    '\n\nOnly include things NOT already in that list (or where status meaningfully changed). For each: institution, program name, degree levels, whether founded after ~2014, current status, short note, source URL. NEVER invent a source URL. Return ONLY the structured object.',
    { label: 'gap:' + l.key, phase: 'Find gaps', schema: LIST_SCHEMA, agentType: 'general-purpose' }
  ).then(r => ({ lens: l.key, programs: r.programs || [] })).catch(() => null)
))

const norm = s => (s || '').toLowerCase().replace(/[^a-z0-9]/g, '')
const archSet = new Set(archived.map(norm))
const seen = new Map()
for (const f of found.filter(Boolean)) for (const p of f.programs) {
  const k = norm(p.institution)
  if (!k || archSet.has(k)) continue
  if (!seen.has(k)) seen.set(k, { ...p, lenses: [f.lens] })
  else seen.get(k).lenses.push(f.lens)
}
const merged = [...seen.values()]
const newSince2014 = merged.filter(p => p.founded_after_2014 === 'yes')
log(`Found ${merged.length} programs not in the archive (${newSince2014.length} founded after ~2014).`)
return { gaps: merged, newSince2014, byLens: found.filter(Boolean).map(f => ({ lens: f.lens, count: f.programs.length })) }
