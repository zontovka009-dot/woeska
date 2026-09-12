import {create} from 'zustand'; import type {User} from '../types/user'; type S={user:User|null;setUser:(u:User)=>void}; export const useAuth=create<S>(set=>({user:null,setUser:user=>set({user})}));
