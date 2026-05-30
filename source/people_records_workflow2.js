export const meta = {
  name: 'people-records-verify-2',
  description: 'Verify accurate current records (role, institution, education, status, source) for a list of metals/jewelry educators Phil named.',
  phases: [{ title: 'Research people' }],
}
const PEOPLE = [{"name": "Michael Gayk", "hint": "Metalsmith/jeweler. Education: BFA from College for Creative Studies (Detroit); MFA in Metals from University of Washington. Taught jewelry/metals at Kendall College of Art and Design (KCAD), Grand Rapids, circa 2005. Now based in TEXAS — find his CURRENT institution/role (he may teach jewelry/metals/3D or related). Site: https://www.michaelgayk.com . Confirm current TX role + education + permalink."}, {"name": "Courtney Starrett", "hint": "Metalsmith/jeweler/designer. Education: BFA University of Kansas; MFA Tyler School of Art (Temple University). Taught at Kendall College of Art and Design (KCAD) circa 2005. Now based in TEXAS — find current institution/role (e.g., Texas Tech or other). Site: http://www.courtneystarrett.com . Confirm current TX role + education + permalink."}, {"name": "Richard Elaver", "hint": "Now teaches PRODUCT/Industrial Design at Appalachian State University (Boone, NC). MFA in METALS from Cranbrook Academy of Art. Taught at Kendall College of Art and Design (KCAD) for a summer circa 2007. Confirm his current App State title + Cranbrook metals MFA + undergrad + a appstate.edu permalink."}, {"name": "Frankie Flood", "hint": "At Appalachian State University (Boone, NC) — directs/teaches metals/jewelry and digital fabrication/sculpture. Previously University of Wisconsin-Milwaukee and UNC Charlotte. Find current App State title, education (degrees/schools), and an appstate.edu permalink."}]
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
