import {defineStore} from 'pinia'
import {ref} from 'vue'
import {api,setCsrf} from '../api/client'
import type {Me,FamilyInfo} from '../types'
export const useGuest=defineStore('guest',()=>{
 const me=ref<Me|null>(null),families=ref<FamilyInfo[]>([]),error=ref(''),ready=ref(false)
 async function refresh(){me.value=await api<Me>('/me');setCsrf(me.value.csrf_token)}
 async function init(){try{const g=await api<{csrf_token:string}>('/guest','POST');setCsrf(g.csrf_token);await refresh();families.value=await api<FamilyInfo[]>('/families');ready.value=true;error.value=''}catch(e){error.value=(e as Error).message}}
 return {me,families,error,ready,init,refresh}
})
