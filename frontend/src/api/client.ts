let csrf=''
export function setCsrf(value:string){csrf=value}
export async function api<T>(path:string,method='GET',body?:unknown,key?:string):Promise<T>{
 const headers:Record<string,string>={}
 if(method!=='GET'){headers['Content-Type']='application/json';headers['X-CSRF-Token']=csrf;if(key)headers['Idempotency-Key']=key}
 const response=await fetch('/api/v1'+path,{method,headers,credentials:'same-origin',body:method==='GET'?undefined:JSON.stringify(body??{})})
 let data
 try{data=await response.json()}catch{throw new Error('The server could not be reached. Your saved progress is safe.')}
 if(!response.ok)throw new Error(data.error?.message??'The request could not be completed.')
 return data as T
}
export function requestKey(){return crypto.randomUUID()}
export function parseInput(raw:string,list:boolean):number|number[]{
 if(!list){if(!/^-?\d+$/.test(raw.trim()))throw new Error('Enter one whole number.');return Number(raw)}
 const trimmed=raw.trim().replace(/^\[/,'').replace(/\]$/,'').trim()
 if(!trimmed)return []
 const parts=trimmed.split(',').map(x=>x.trim())
 if(!parts.every(x=>/^-?\d+$/.test(x)))throw new Error('Enter whole numbers separated by commas, such as 3, -2, 4.')
 return parts.map(Number)
}
