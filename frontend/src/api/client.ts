const base=import.meta.env.VITE_API_URL||'';
let token=localStorage.getItem('wathis_token')||'';
export function setToken(value:string){token=value; if(value)localStorage.setItem('wathis_token',value);else localStorage.removeItem('wathis_token')}
export function getToken(){return token}
export async function api<T>(path:string,options:RequestInit={}):Promise<T>{const headers:any={'Content-Type':'application/json',...(options.headers||{})};if(token)headers.Authorization=`Bearer ${token}`;const r=await fetch(base+path,{...options,headers});if(!r.ok)throw new Error(await r.text());return r.json() as Promise<T>}
