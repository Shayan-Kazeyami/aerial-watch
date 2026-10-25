import * as THREE from './vendor/three.module.js';
import {createSecondsDetails} from './assembly-seconds-details.js';

// Display-only printing above the supplied dial. Coordinates are millimetres in
// the native dial plane; no source part or source geometry is modified.
export const DIAL_LAYOUT = Object.freeze({
  radius: 16.44,
  // Extruded open-work rings reach 3.522 including their bevel thickness.
  height: 3.55,
  arborRadius: 1.08,
  seconds: Object.freeze({x: -7.9988, y: -.01629, arborRadius: .215, radius: 4.37}),
  track: Object.freeze({inner: 15.39, outer: 15.92}),
});

export function createDialDetails({renderer, openWork=false, canvasFactory = () => document.createElement('canvas')} = {}) {
  const canvas = canvasFactory();
  canvas.width = canvas.height = 2048;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('A 2D canvas is required to print the dial.');
  const radius = DIAL_LAYOUT.radius, unit = canvas.width / (2 * radius);
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.scale(unit, -unit);
  ctx.lineCap = 'round';
  const ink = openWork?'#e3dfcf':'#253442', muted = openWork?'#b8beb7':'#667078', groove = openWork?'rgba(210,214,202,.30)':'rgba(77,84,87,.21)';
  const circle = (x, y, r, width, color = ink) => {
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.lineWidth = width; ctx.strokeStyle = color; ctx.stroke();
  };
  const line = (x1, y1, x2, y2, width, color = ink) => {
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
    ctx.lineWidth = width; ctx.strokeStyle = color; ctx.stroke();
  };
  const text = (label, x, y, size, {color = ink, family = 'Arial', weight = '400', tracking = 0} = {}) => {
    ctx.save(); ctx.translate(x, y); ctx.scale(1, -1);
    ctx.font = `${weight} ${size}px ${family}`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = color;
    if (!tracking) ctx.fillText(label, 0, 0);
    else {
      const widths = [...label].map(char => ctx.measureText(char).width);
      let left = -(widths.reduce((sum, width) => sum + width, 0) + tracking * (widths.length - 1)) / 2;
      ctx.textAlign = 'left';
      [...label].forEach((char, index) => {ctx.fillText(char, left, 0); left += widths[index] + tracking;});
    }
    ctx.restore();
  };

  // A true railway: all sixty divisions lie between two fine, closed rings.
  const {inner, outer} = openWork?{inner:15.65,outer:16.10}:DIAL_LAYOUT.track;
  circle(0, 0, inner, .028); circle(0, 0, outer, .028);
  for (let minute = 0; minute < 60; minute++) {
    const angle = minute * Math.PI / 30, major = minute % 5 === 0;
    const start = major ? inner : outer - .23;
    line(Math.sin(angle) * start, Math.cos(angle) * start,
      Math.sin(angle) * outer, Math.cos(angle) * outer, major ? .065 : .032);
  }
  const cardinalRadius=openWork?15.03:13.85;
  for (const [label, x, y] of [['12', 0, cardinalRadius], ['3', cardinalRadius, 0], ['6', 0, -cardinalRadius], ['9', -cardinalRadius, 0]]) {
    text(label, x, y, openWork?1.08:1.68, {family:openWork?'Arial':'Georgia',weight:openWork?'500':'400'});
  }

  text('AERIAL', openWork?0:2.7, openWork?13.45:6.25, openWork?.92:1.02, {weight: '500', tracking: openWork?.23:.30});
  text('CALIBRE OM10', openWork?0:2.7, openWork?12.70:4.82, openWork?.29:.43, {color: muted, tracking: .105});
  if(!openWork) {
    line(1.65, -7.1, 3.75, -7.1, .025, muted);
    text('MANUAL WINDING', 2.7, -8.02, .37, {color: muted, tracking: .065});
  }

  const seconds = DIAL_LAYOUT.seconds;
  if (!openWork) {
  circle(seconds.x, seconds.y, openWork?4.10:seconds.radius, .035, muted);
  if(!openWork) circle(seconds.x, seconds.y, seconds.radius - .13, .025, groove);
  circle(seconds.x, seconds.y, openWork?3.63:3.83, .022, muted);
  // Fine concentric printing catches the stepped subdial without obscuring the
  // existing sixty applied second marks at radius 3.5 mm.
  if(!openWork) for (let r = .55; r < 2.22; r += .105) circle(seconds.x, seconds.y, r, .018, groove);
  if(openWork) for(let i=0;i<60;i++) {
    const a=i*Math.PI/30,r=i%5===0?3.91:4.00;
    line(seconds.x+Math.sin(a)*r,seconds.y+Math.cos(a)*r,seconds.x+Math.sin(a)*4.12,seconds.y+Math.cos(a)*4.12,i%5===0?.045:.022,muted);
  }
  const numberRadius=openWork?3.77:2.75;
  for (const [label, dx, dy] of [['60', 0, numberRadius], ['15', numberRadius, 0], ['30', 0, -numberRadius], ['45', -numberRadius, 0]]) {
    text(label, seconds.x + dx, seconds.y + dy, openWork?.27:.47, {color: muted});
  }

  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = Math.min(8, renderer?.capabilities?.getMaxAnisotropy?.() || 1);
  const material = new THREE.MeshStandardMaterial({
    // Alpha-tested ink participates in the opaque transmission capture. A
    // blended decal behind the sapphire would be skipped by that capture and
    // then hidden by the crystal's depth in the later transparent pass.
    map: texture, color: 0xffffff, transparent: false, alphaTest: .1, alphaToCoverage: true,
    metalness: .05, roughness: .62, depthWrite: true,
    polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
  });
  const shape = new THREE.Shape();
  shape.absarc(0, 0, radius, 0, Math.PI * 2, false);
  for (const hole of [{x: 0, y: 0, radius: DIAL_LAYOUT.arborRadius},
    {x: seconds.x, y: seconds.y, radius: seconds.arborRadius}]) {
    const path = new THREE.Path();
    path.absarc(hole.x, hole.y, hole.radius, 0, Math.PI * 2, true);
    shape.holes.push(path);
  }
  const geometry = new THREE.ShapeGeometry(shape, 128);
  // ShapeGeometry supplies world-coordinate UVs. Normalize them to the print.
  const uv = geometry.getAttribute('uv');
  for (let index = 0; index < uv.count; index++) {
    uv.setXY(index, THREE.MathUtils.clamp(uv.getX(index) / (2 * radius) + .5, 0, 1),
      THREE.MathUtils.clamp(uv.getY(index) / (2 * radius) + .5, 0, 1));
  }
  const print = new THREE.Mesh(geometry, material);
  print.name = 'Aerial precision dial printing';
  print.rotation.x = -Math.PI / 2;
  print.position.y = DIAL_LAYOUT.height;
  print.renderOrder = 1;
  print.userData.displayDetail = true;
  const group = new THREE.Group();
  group.name = 'Aerial dial surface details'; group.add(print);
  const secondsDetails = openWork ? createSecondsDetails({canvasFactory, renderer, height:DIAL_LAYOUT.height}) : null;
  if(secondsDetails) group.add(secondsDetails.group);
  let disposed = false;
  return {group, texture, dispose() {
    if (disposed) return;
    disposed = true; secondsDetails?.dispose(); geometry.dispose(); material.dispose(); texture.dispose();
    group.removeFromParent();
  }};
}
