export type Family = 'dependencies'|'logic'|'ordering'|'induction'|'hypothesis'
export type Mode = 'mixed'|'focus'|'check'|'probe'
export type Value = number|number[]|string|boolean|Record<string,string>|null
export interface Rule {id:string;label:string}
export interface Observation {input:number|number[];output:number|number[]}
export interface Render {kind:string;courses?:number[];edges?:{prerequisite:number;course:number}[];people?:{id:string;name:string;statement:string}[];labels?:string[];premises?:string[];claim?:string;candidates?:Rule[];examples?:Observation[];target?:number|number[];input_kind?:'number'|'list';presentation?:string;schedule_rows?:{task:string;prerequisites:string[]}[]}
export interface Explanation {steps:string[];answer:Value;source:string;adapter_version:string;witness?:{order?:number[];cycle?:number[];orders?:string[][]};truth_table?:{roles:string[];statements:boolean[];consistent:boolean}[]}
export interface Attempt {id:string;family:Family;difficulty:number;mode:Mode;session_id:string;created:number;assisted:boolean;correct:boolean|null;confidence:number|null;reflection:{category?:string|null;note?:string};sealed:boolean;provenance:string;answer?:Value;explanation?:Explanation;task?:Task}
export interface Task {instance_id:string;family:Family;difficulty:number;instructions:string;render:Render;response_schema:{kind:string};session_id:string;mode:Mode;hints_used:number;hints?:string[];queries:Observation[];draft:{scratchpad?:string;answer?:Value;confidence?:number|null};rationale:string;position:number;total:number;submitted:boolean;state:string;feedback_sealed:boolean;result?:Attempt}
export interface TrainingSession {id:string;mode:Mode;family:Family|null;state:string;total:number;completed:number;current:Task|null;released:boolean;manifest:{version?:string;form?:string;transfer_type?:string;prior_releases?:number;repeated_form?:boolean}}
export interface FamilyInfo {id:Family;name:string;lesson:{principle:string;example:string;strategy:string};levels:number}
export interface Me {guest:boolean;csrf_token:string;admin:boolean;levels:Partial<Record<Family,number>>;sessions:{id:string;mode:Mode;state:string}[]}
export const names:Record<Family,string>={dependencies:'Dependency reasoning',logic:'Logical consistency',ordering:'Relational ordering',induction:'Rule induction',hypothesis:'Hypothesis testing'}
export const date=(t:number)=>new Date(t*1000).toLocaleDateString(undefined,{month:'short',day:'numeric'})
export const display=(v:unknown):string=>Array.isArray(v)?`[${v.join(', ')}]`:typeof v==='object'&&v!==null?Object.entries(v).map(([k,v])=>`${k}: ${v}`).join(' · '):String(v)
