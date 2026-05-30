export const meta = {
  name: 'people-records-verify',
  description: 'Verify accurate current records (role, institution, education, status, source) for a list of metals/jewelry educators Phil named.',
  phases: [{ title: 'Research people' }],
}
const PEOPLE = [{"name": "Kristin Beeler", "hint": "In our DB at Long Beach City College, CA. Phil says she has relocated to SCOTLAND. Confirm her CURRENT role/location (Scotland?) and her education."}, {"name": "Ana Lopez", "hint": "Metalsmith/jeweler educator. Find current institution/role, education, location. (Possibly UK/US — disambiguate the metals/jewelry one.)"}, {"name": "Anya Kivarkis", "hint": "DB: Professor, University of Oregon jewelry/metals. Confirm current role + education (degrees/schools)."}, {"name": "Haley Bates", "hint": "DB: Colorado State University metals/jewelry. Confirm current role + education."}, {"name": "Motoko Furuhashi", "hint": "DB: New Mexico State University metals/jewelry. Confirm current role + education."}, {"name": "Mary Hallam Pearse", "hint": "Metalsmith/jeweler, likely University of Georgia (Lamar Dodd). Confirm current role + education."}, {"name": "Cappy Counard", "hint": "DB: Edinboro University of Pennsylvania metals/jewelry. Confirm whether she/the program is still active (Edinboro had program cuts) + education."}, {"name": "Renee Zettle-Sterling", "hint": "DB: Grand Valley State University metals/jewelry. Confirm current role + education."}, {"name": "Jill Baker Gower", "hint": "IMPORTANT: our DB has a COLLISION — one row puts her at 'College of DuPage' which is a DIFFERENT person (a different Jill Gower). The metals/jewelry Jill Baker Gower is at ROWAN UNIVERSITY (formerly Glassboro State), NJ. Confirm her correct current institution/role + education, and note the College-of-DuPage row is a different person."}, {"name": "Erica Meier", "hint": "Metalsmith/jeweler educator. Find current institution/role + education. Disambiguate (not the nonprofit exec of same name)."}, {"name": "Lauren Selden", "hint": "DB: Stephen F. Austin State University metals/jewelry. Confirm current role + education."}, {"name": "Natalie Macellaio", "hint": "Metalsmith/jeweler educator. Find current institution/role + education."}, {"name": "Becky McDonah", "hint": "DB: Millersville University metals/jewelry. Confirm current role + education."}, {"name": "Adam Hawk", "hint": "Metalsmith/jeweler educator. Find current institution/role + education."}, {"name": "Stephen Saracino", "hint": "Longtime SUNY Buffalo State metals/jewelry professor, now RETIRED (Phil confirms). Confirm retirement/emeritus status + education; what year retired if findable."}]
const SCHEMA = {
  type:'object', additionalProperties:false,
  required:['name','isMetalsJewelryPerson','currentRole','currentInstitution','status','location','education','bestUrl','sources','confidence','note'],
  properties:{
    name:{type:'string'},
    isMetalsJewelryPerson:{type:'boolean'},
    currentRole:{type:'string', description:'current job title + institution, one line'},
    currentInstitution:{type:'string'},
    status:{type:'string', enum:['active','retired','relocated','deceased','unknown']},
    location:{type:'string'},
    education:{type:'array', items:{type:'object', additionalProperties:false, required:['level','school'],
      properties:{ level:{type:'string'}, school:{type:'string'}, degree:{type:'string'}, year:{type:'string'} }}},
    bestUrl:{type:'string', description:'permalink to institution faculty page or their own site'},
    sources:{type:'array', items:{type:'string'}},
    confidence:{type:'string', enum:['high','medium','low']},
    note:{type:'string'},
  }
}
function prompt(p){
  return `Get an ACCURATE, sourced current record for this metals/jewelry educator for a directory.

PERSON: ${p.name}
CONTEXT: ${p.hint}

Find: their CURRENT role + institution (2025-2026), status (active/retired/relocated/deceased), location, and their EDUCATION (degrees + schools + years if findable). Provide a permalink (institution faculty page preferred, or their own site) + any corroborating sources.

RULES: institution's own page first; never invent a URL or a degree; confirm it is the metalsmith/jeweler (disambiguate same-name people); honest 'unknown'/'low' when unsure; state what they ARE/WERE doing. If a provided 'current' fact looks wrong, correct it and say so in note.`
}
phase('Research people')
const out = await parallel(PEOPLE.map(p => () => agent(prompt(p), {schema:SCHEMA, phase:'Research people', label:p.name}).then(v=>v?{...v,_hint:p.hint}:null)))
return { records: out.filter(Boolean) }
