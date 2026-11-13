// Derived from official Three.js r187 transmission TSL (MIT, Three.js Authors).
// Local changes mirror assembly-refraction.js: edge coverage and sampling-only
// roughness-floor removal. Reflection/Fresnel still receive physical roughness.
import {PhysicalLightingModel,BackSide} from './vendor/three.webgpu.js';
import * as T from './vendor/three.tsl.js';
const {Fn,vec2,vec3,vec4,refract,normalize,div,length,clamp,viewportMipTexture,viewportOpaqueMipTexture,cameraViewport,screenSize,log2,textureBicubicLevel,If,log,exp,Loop,EnvironmentBRDF,materialReference,max,min,smoothstep,float,positionWorld,cameraPosition,normalWorld,roughness,diffuseContribution,specularColorBlended,specularF90,modelWorldMatrix,cameraViewMatrix,cameraProjectionMatrix,ior,thickness,attenuationColor,attenuationDistance,dispersion,transmission,diffuseColor,mix}=T;
const getVolumeTransmissionRay = /*@__PURE__*/ Fn( ( [ n, v, thickness, ior, modelMatrix ] ) => {

	// Direction of refracted light.
	const refractionVector = vec3( refract( v.negate(), normalize( n ), div( 1.0, ior ) ) );

	// Compute rotation-independent scaling of the model matrix.
	const modelScale = vec3(
		length( modelMatrix[ 0 ].xyz ),
		length( modelMatrix[ 1 ].xyz ),
		length( modelMatrix[ 2 ].xyz )
	);

	// The thickness is specified in local space.
	return normalize( refractionVector ).mul( thickness.mul( modelScale ) );

}, {
	n: 'vec3',
	v: 'vec3',
	thickness: 'float',
	ior: 'float',
	modelMatrix: 'mat4',
	return: 'vec3'
} );

const applyIorToRoughness = /*@__PURE__*/ Fn( ( [ roughness, ior ] ) => {

	// Scale roughness with IOR so that an IOR of 1.0 results in no microfacet refraction and
	// an IOR of 1.5 results in the default amount of microfacet refraction.
	return roughness.mul( clamp( ior.mul( 2.0 ).sub( 2.0 ), 0.0, 1.0 ) );

}, { roughness: 'float', ior: 'float', return: 'float' } );

const viewportBackSideTexture = /*@__PURE__*/ viewportMipTexture();
const viewportFrontSideTexture = /*@__PURE__*/ viewportOpaqueMipTexture();

const getTransmissionSample = /*@__PURE__*/ Fn( ( [ fragCoord, roughness, ior, entryUV, clipW ], { material, renderer } ) => {

	const dedicated=renderer.aerialTransmissionNode;
	const vTexture = dedicated || (material.side === BackSide ? viewportBackSideTexture : viewportFrontSideTexture);

	const authored=materialReference('roughness','float');
	const samplingRoughness=material.userData.aerialRefraction?.clearTransmission?clamp(authored.add(max(0,roughness.sub(max(authored,.045)))),0,1):roughness;
	const size=dedicated?T.textureSize(dedicated):cameraViewport.zw;
	const edge=min(fragCoord,vec2(1).sub(fragCoord)).mul(size);
	const feather=clamp(length(fragCoord.sub(entryUV).mul(size)),4,64);
	const coverage=clipW.greaterThan(.00001).select(smoothstep(1,feather,min(edge.x,edge.y)),float(0));
	const low=vec2(1).div(size),high=vec2(1).sub(low);
	const safeUV=clamp(fragCoord,low,high),safeEntry=clamp(entryUV,low,high);
	const lod=log2(size.x).mul(applyIorToRoughness(samplingRoughness,ior));
	const sample=uv=>textureBicubicLevel(vTexture.sample(dedicated?uv:uv.mul(cameraViewport.zw).add(cameraViewport.xy).div(screenSize)),lod);
	return mix(sample(safeEntry),sample(safeUV),coverage);

} );

const volumeAttenuation = /*@__PURE__*/ Fn( ( [ transmissionDistance, attenuationColor, attenuationDistance ] ) => {

	If( attenuationDistance.notEqual( 0 ), () => {

		// Compute light attenuation using Beer's law.
		const attenuationCoefficient = log( attenuationColor ).negate().div( attenuationDistance );
		const transmittance = exp( attenuationCoefficient.negate().mul( transmissionDistance ) );

		return transmittance;

	} );

	// Attenuation distance is +∞, i.e. the transmitted color is not attenuated at all.
	return vec3( 1.0 );

}, { transmissionDistance: 'float', attenuationColor: 'vec3', attenuationDistance: 'float', return: 'vec3' } );

const getIBLVolumeRefraction = /*@__PURE__*/ Fn( ( [ n, v, roughness, diffuseColor, specularColor, specularF90, position, modelMatrix, viewMatrix, projMatrix, ior, thickness, attenuationColor, attenuationDistance, dispersion ] ) => {

	let transmittedLight, transmittance;
	const entryClip=projMatrix.mul(viewMatrix.mul(vec4(position,1)));
	const entry=entryClip.xy.div(entryClip.w).mul(.5).add(.5);
	const entryUV=vec2(entry.x,entry.y.oneMinus());

	if ( dispersion ) {

		transmittedLight = vec4().toVar();
		transmittance = vec3().toVar();

		const halfSpread = ior.sub( 1.0 ).mul( dispersion.mul( 0.025 ) );
		const iors = vec3( ior.sub( halfSpread ), ior, ior.add( halfSpread ) );

		Loop( { start: 0, end: 3 }, ( { i } ) => {

			const ior = iors.element( i );

			const transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			const refractedRayExit = position.add( transmissionRay );

			// Project refracted vector on the framebuffer, while mapping to normalized device coordinates.
			const ndcPos = projMatrix.mul( viewMatrix.mul( vec4( refractedRayExit, 1.0 ) ) );
			const refractionCoords = vec2( ndcPos.xy.div( ndcPos.w ) ).toVar();
			refractionCoords.addAssign( 1.0 );
			refractionCoords.divAssign( 2.0 );
			refractionCoords.assign( vec2( refractionCoords.x, refractionCoords.y.oneMinus() ) ); // webgpu

			// Sample framebuffer to get pixel the refracted ray hits.
			const transmissionSample = getTransmissionSample( refractionCoords, roughness, ior, entryUV, ndcPos.w );

			transmittedLight.element( i ).assign( transmissionSample.element( i ) );
			transmittedLight.a.addAssign( transmissionSample.a );

			transmittance.element( i ).assign( diffuseColor.element( i ).mul( volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance ).element( i ) ) );

		} );

		transmittedLight.a.divAssign( 3.0 );

	} else {

		const transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
		const refractedRayExit = position.add( transmissionRay );

		// Project refracted vector on the framebuffer, while mapping to normalized device coordinates.
		const ndcPos = projMatrix.mul( viewMatrix.mul( vec4( refractedRayExit, 1.0 ) ) );
		const refractionCoords = vec2( ndcPos.xy.div( ndcPos.w ) ).toVar();
		refractionCoords.addAssign( 1.0 );
		refractionCoords.divAssign( 2.0 );
		refractionCoords.assign( vec2( refractionCoords.x, refractionCoords.y.oneMinus() ) ); // webgpu

		// Sample framebuffer to get pixel the refracted ray hits.
		transmittedLight = getTransmissionSample( refractionCoords, roughness, ior, entryUV, ndcPos.w );
		transmittance = diffuseColor.mul( volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance ) );

	}

	const attenuatedColor = transmittance.rgb.mul( transmittedLight.rgb );
	const dotNV = n.dot( v ).clamp();

	// Get the specular component.
	const F = vec3( EnvironmentBRDF( { // n, v, specularColor, specularF90, roughness
		dotNV,
		specularColor,
		specularF90,
		roughness
	} ) );

	// As less light is transmitted, the opacity should be increased. This simple approximation does a decent job
	// of modulating a CSS background, and has no effect when the buffer is opaque, due to a solid object or clear color.
	const transmittanceFactor = transmittance.r.add( transmittance.g, transmittance.b ).div( 3.0 );

	return vec4( F.oneMinus().mul( attenuatedColor ), transmittedLight.a.oneMinus().mul( transmittanceFactor ).oneMinus() );

} );


class AerialPhysicalLightingModel extends PhysicalLightingModel {
 start(builder){
  const enabled=this.transmission;this.transmission=false;
  try{super.start(builder);}finally{this.transmission=enabled;}
  if(enabled){
   builder.context.backdrop=getIBLVolumeRefraction(normalWorld,cameraPosition.sub(positionWorld).normalize(),roughness,diffuseContribution,specularColorBlended,specularF90,positionWorld,modelWorldMatrix,cameraViewMatrix,cameraProjectionMatrix,ior,thickness,attenuationColor,attenuationDistance,this.dispersion?dispersion:null);
   builder.context.backdropAlpha=transmission;
   diffuseColor.a.mulAssign(mix(1,builder.context.backdrop.a,transmission));
  }
 }
}
export function applyNodeRefraction(node,source){
 if(!source.userData.aerialRefraction)return node;
 node.setupLightingModel=function(){return new AerialPhysicalLightingModel(this.useClearcoat,this.useSheen,this.useIridescence,this.useAnisotropy,this.useTransmission,this.useDispersion,this.useRetroreflection,this.useDiffuseRoughness);};
 return node;
}
