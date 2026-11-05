// Render the complete pipeline at one deliberate resolution. Canvas MSAA alone
// cannot sharpen an undersampled offscreen scene or the sapphire's refraction.
export const RENDER_PROFILES=Object.freeze({
  balanced:{label:'Balanced',pixelRatio:1.5,minimumPixelRatio:1.5,maxPixels:4500000,ao:true,shadows:true,samples:4,transmissionScale:1},
  detail:{label:'High definition',pixelRatio:2.5,minimumPixelRatio:2.5,preserveNative:true,maxPixels:8000000,maxTransmissionPixels:12000000,ao:true,shadows:true,samples:4,transmissionScale:2},
  studio:{label:'Studio supersampling',pixelRatio:3,minimumPixelRatio:3,preserveNative:true,maxPixels:12000000,maxTransmissionPixels:16000000,ao:true,shadows:true,samples:4,transmissionScale:2},
  efficient:{label:'Smoother motion',pixelRatio:1,minimumPixelRatio:1,maxPixels:2500000,ao:false,shadows:false,samples:0,transmissionScale:1},
});
export function resolveRenderResolution({width,height,devicePixelRatio=1,quality='detail',maxTextureSize=16384,maxSamples=4}={}){
  if(!(width>0&&height>0&&Number.isFinite(width)&&Number.isFinite(height)))throw new TypeError('Positive finite stage dimensions required.');
  const profile=RENDER_PROFILES[quality];if(!profile)throw new TypeError('Unknown render quality.');
  const native=Number.isFinite(devicePixelRatio)&&devicePixelRatio>0?devicePixelRatio:1;
  // Quality/capture modes must not quietly undersample a native3×/4× panel.
  // The existing pixel/texture budgets still cap unusually large buffers;
  // explicitly economical modes retain their lower, intentional resolution.
  const requested=profile.preserveNative?Math.max(native,profile.pixelRatio):Math.min(Math.max(native,profile.minimumPixelRatio),profile.pixelRatio);
  const limit=Math.min(Math.sqrt(profile.maxPixels/(width*height)),maxTextureSize/Math.max(width,height));
  const pixelRatio=Math.min(requested,limit);
  // Sharp sapphire needs its own sampled background budget. Limit that buffer
  // independently so glass cannot silently lower the complete scene's native
  // pixel density on a large/high-DPI display.
  const transmissionScale=Math.min(profile.transmissionScale,
    Math.sqrt((profile.maxTransmissionPixels||profile.maxPixels)/(width*height*pixelRatio*pixelRatio)),
    maxTextureSize/(Math.max(width,height)*pixelRatio));
  return {pixelRatio,width:Math.floor(width*pixelRatio),height:Math.floor(height*pixelRatio),
    samples:Math.min(profile.samples,Math.max(0,maxSamples)),transmissionScale,
    requestedTransmissionScale:profile.transmissionScale,transmissionLimited:transmissionScale<profile.transmissionScale,
    requestedPixelRatio:requested,limited:pixelRatio<requested};
}
