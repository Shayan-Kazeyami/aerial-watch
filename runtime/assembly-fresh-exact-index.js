import {createQualityDesign} from './assembly-design.js';
import {createLowerCarrierGoldZone} from './assembly-lower-carrier-gold.js';
import {compactPrivateIndex} from './assembly-fresh-gold-index.js';
import {indexFreshQuality} from './assembly-fresh-quality-index.js';
import {expected} from './assembly-fresh-quality-fingerprints.js';
import {hashBytes} from './assembly-fresh-byte-hash.js';
// Calls occur synchronously during fresh construction, before scene exposure/render.
// Default OFF; current caller explicitly opts into the verified cohort only.
export function createFreshIndexedQuality(source,exterior,{enabled=false}={}){
 const owner=createQualityDesign(source,exterior);
 try{if(enabled===true)indexFreshQuality(owner,{flags:Object.fromEntries(Object.keys(expected).map(name=>[name,true])),expected,hashBytes});return owner;}
 catch(error){owner.dispose();throw error;}
}
export function createFreshIndexedGold(mesh,gold,options,{enabled=false}={}){
 const owner=createLowerCarrierGoldZone(mesh,gold,options);
 try{compactPrivateIndex(owner.derived,{enabled:enabled===true});return owner;}
 catch(error){owner.dispose();throw error;}
}
