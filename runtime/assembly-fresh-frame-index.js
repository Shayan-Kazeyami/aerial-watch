import {createOpenFrontFrame} from './assembly-open-front.js';
import {indexFreshQuality} from './assembly-fresh-quality-index.js';
import {expected} from './assembly-fresh-frame-fingerprints.js';
import {hashBytes} from './assembly-fresh-byte-hash.js';
// Fresh construction only. Default OFF. No await or scene exposure before compaction.
export function createFreshIndexedFrame({enabled=false}={}){
 const owner=createOpenFrontFrame();
 try { if(enabled===true) indexFreshQuality({...owner,meshes:[...owner.group.children]}, {flags:Object.fromEntries(Object.keys(expected).map(name=>[name,true])),expected,hashBytes}); return owner; }
 catch(error){owner.dispose();throw error;}
}
