import * as THREE from './vendor/three.module.js';
// Local non-indexed merger keeps browser and Node imports on the same Three build.
function mergeGeometries(parts) {
  const geometry=new THREE.BufferGeometry();
  for(const name of ['position','normal','uv']) {
    const size=parts[0].attributes[name].itemSize;
    const data=new Float32Array(parts.reduce((n,p)=>n+p.attributes[name].array.length,0));
    let offset=0;for(const part of parts){data.set(part.attributes[name].array,offset);offset+=part.attributes[name].array.length;}
    geometry.setAttribute(name,new THREE.BufferAttribute(data,size));
  }
  return geometry;
}
import {OPEN_FRONT_LAYOUT} from './assembly-open-front.js';

// Fine real solids replace the subdial's former 1.4-pixel-wide raster ticks.
// Native XY, axial Z; merged rails/ticks incur one draw, independent of count.
export const SECONDS_DETAIL_LAYOUT=Object.freeze({innerRail:3.63,outerRail:4.10,
  innerWidth:.022,outerWidth:.035,depth:.006,segments:384,numeralRadius:3.77,numeralSize:.27});
export function createSecondsDetails({canvasFactory,renderer,height=3.55}) {
  const s=OPEN_FRONT_LAYOUT.seconds,l=SECONDS_DETAIL_LAYOUT,parts=[];
  for(const [radius,width] of [[l.innerRail,l.innerWidth],[l.outerRail,l.outerWidth]]) {
    const shape=new THREE.Shape();shape.absarc(0,0,radius+width/2,0,Math.PI*2,false);
    const hole=new THREE.Path();hole.absarc(0,0,radius-width/2,0,Math.PI*2,true);shape.holes.push(hole);
    parts.push(new THREE.ExtrudeGeometry(shape,{depth:l.depth,bevelEnabled:false,curveSegments:l.segments}));
  }
  for(let i=0;i<60;i++) {
    const angle=i*Math.PI/30,major=i%5===0,start=major?3.91:4.00,end=4.12;
    const tick=new THREE.BoxGeometry(major?.045:.022,end-start,l.depth).toNonIndexed();
    tick.translate(0,(start+end)/2,l.depth/2);tick.rotateZ(-angle);parts.push(tick);
  }
  const geometry=mergeGeometries(parts,false);parts.forEach(g=>g.dispose());
  const material=new THREE.MeshStandardMaterial({color:0xb8beb7,metalness:.05,roughness:.62});
  const rails=new THREE.Mesh(geometry,material);rails.name='Seconds / two solid rails and sixty merged divisions';
  rails.userData.displayDetail=true;
  const group=new THREE.Group();group.name='Seconds / precision geometry and local numeral atlas';
  group.rotation.x=-Math.PI/2;group.position.set(s.x,height,-s.y);group.add(rails);

  // Four small local glyph patches give 320px/mm, versus 62px/mm on the
  // whole-face atlas, using only 1MiB RGBA. Transparent pixels never seal holes.
  const canvas=canvasFactory();canvas.width=1024;canvas.height=256;
  const ctx=canvas.getContext('2d');if(!ctx)throw new Error('A 2D canvas is required for seconds numerals.');
  ctx.fillStyle='#b8beb7';ctx.font=`400 ${l.numeralSize*320}px Arial`;
  ctx.textAlign='center';ctx.textBaseline='middle';
  ['60','15','30','45'].forEach((label,i)=>ctx.fillText(label,128+i*256,128));
  const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
  texture.anisotropy=Math.min(8,renderer?.capabilities?.getMaxAnisotropy?.()||1);
  const numeralMaterial=new THREE.MeshStandardMaterial({map:texture,color:0xffffff,alphaTest:.1,alphaToCoverage:true,
    metalness:.05,roughness:.62,depthWrite:true});
  const patches=[];
  for(const [i,x,y] of [[0,0,l.numeralRadius],[1,l.numeralRadius,0],[2,0,-l.numeralRadius],[3,-l.numeralRadius,0]]) {
    const patch=new THREE.PlaneGeometry(.8,.8).toNonIndexed(),uv=patch.attributes.uv;
    for(let j=0;j<uv.count;j++)uv.setX(j,(uv.getX(j)+i)/4);
    patch.translate(x,y,0);patches.push(patch);
  }
  const numeralGeometry=mergeGeometries(patches,false);patches.forEach(g=>g.dispose());
  const numerals=new THREE.Mesh(numeralGeometry,numeralMaterial);numerals.name='Seconds / high-density numeral printing';
  numerals.userData.displayDetail=true;group.add(numerals);
  let disposed=false;
  return {group,geometry,texture,dispose(){if(disposed)return;disposed=true;
    [geometry,numeralGeometry].forEach(g=>g.dispose());[material,numeralMaterial].forEach(m=>m.dispose());texture.dispose();group.removeFromParent();}};
}
