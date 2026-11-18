// Actual extra scene coverage; not ray tracing or a solution for hidden surfaces.
export function overscanPlan({width,height,pixelRatio=1,margin=.12,maxTextureSize=8192,transmissionScale=2,budgetBytes=384*1024*1024,bytesPerPixel=192}={}){
  const w=Math.max(1,Math.floor(width*pixelRatio)),h=Math.max(1,Math.floor(height*pixelRatio));
  const requested=Math.max(0,Math.min(.5,Number(margin)||0));
  const limit=Math.min(maxTextureSize/Math.max(1,transmissionScale)/w,maxTextureSize/Math.max(1,transmissionScale)/h,Math.sqrt(budgetBytes/(w*h*bytesPerPixel)));
  const scale=Math.max(1,Math.min(1+requested*2,limit));
  const renderWidth=Math.max(w,Math.floor(w*scale)),renderHeight=Math.max(h,Math.floor(h*scale));
  return {width:w,height:h,renderWidth,renderHeight,scaleX:renderWidth/w,scaleY:renderHeight/h,crop:[w/renderWidth,h/renderHeight],offset:[(renderWidth-w)/2/renderWidth,(renderHeight-h)/2/renderHeight],requestedMargin:requested,effectiveMargin:(scale-1)/2,estimatedBytes:renderWidth*renderHeight*bytesPerPixel,budgetBytes,baseExceedsBudget:w*h*bytesPerPixel>budgetBytes,limited:scale<1+requested*2};
}
export function withExpandedProjection(camera,plan,render,{background}={}){
  const projection=camera.projectionMatrix.clone(),inverse=camera.projectionMatrixInverse.clone();
  const backdrop=background?.isTexture&&!background.isCubeTexture&&background.mapping===300?background:null;
  const auto=backdrop?.matrixAutoUpdate;
  if(auto)backdrop.updateMatrix();
  const textureMatrix=backdrop?.matrix.clone();
  try{
    if(backdrop){backdrop.matrixAutoUpdate=false;backdrop.matrix.multiply(textureMatrix.clone().set(plan.scaleX,0,(1-plan.scaleX)/2,0,plan.scaleY,(1-plan.scaleY)/2,0,0,1));}
    // Scaling rows, not just focal terms, also handles off-axis projections.
    for(const i of [0,4,8,12])camera.projectionMatrix.elements[i]/=plan.scaleX;
    for(const i of [1,5,9,13])camera.projectionMatrix.elements[i]/=plan.scaleY;
    camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
    return render();
  }finally{camera.projectionMatrix.copy(projection);camera.projectionMatrixInverse.copy(inverse);if(backdrop){backdrop.matrix.copy(textureMatrix);backdrop.matrixAutoUpdate=auto;}}
}

// Clamp the glass target against the actual expanded scene dimensions, not
// the pre-overscan canvas. This never reduces the main scene resolution.
export function resolveTransmissionResolution({renderWidth,renderHeight,requestedScale=1,maxPixels=Infinity,maxTextureSize=Infinity}={}) {
  if(!(renderWidth>0&&renderHeight>0&&Number.isFinite(renderWidth)&&Number.isFinite(renderHeight)))throw new TypeError('Positive finite transmission dimensions required.');
  if(!(requestedScale>0&&Number.isFinite(requestedScale)))throw new TypeError('Positive finite transmission scale required.');
  if(!(maxPixels>=1&&maxTextureSize>=1))throw new TypeError('Positive transmission budgets required.');
  const scale=Math.min(requestedScale,Math.sqrt(maxPixels/(renderWidth*renderHeight)),maxPixels/Math.max(renderWidth,renderHeight),maxTextureSize/Math.max(renderWidth,renderHeight));
  const width=Math.max(1,Math.floor(renderWidth*scale)),height=Math.max(1,Math.floor(renderHeight*scale));
  return {requestedScale,effectiveScale:scale,width,height,pixels:width*height,maxPixels,limited:scale<requestedScale};
}
