export function UserAvatar({name,src}:any){return src?<img className="avatar" src={src} />:<div className="avatar">{String(name||'?').slice(0,1).toUpperCase()}</div>}
