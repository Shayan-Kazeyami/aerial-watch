export const AUTHORED_LEATHER_IDENTITY=Object.freeze({
  "schemaVersion": 1,
  "id": "strap-lug-density-r16",
  "status": "QA-only structured puncture charts plus canonical keeper attributes; not promoted",
  "legacySelection": "craft14",
  "lineage": "Immutable R18 with own-source four-end reconstruction, UV14 chart trajectory mapping, and independently sample-gated density reduction; original sewing retained; UV15 changes only approved outer-chart UV phase; R16 localized rolled-end density pass",
  "thread": {
    "diameterMm": 0.13,
    "crossSection": "constant round",
    "entry": "nominal quarter-turn plus final-body envelope refit; vertical buried stem",
    "entryRadiusMm": 0.1,
    "surfaceCenterLiftMm": 0.066,
    "surfaceCenterLiftScope": "nominal base before actual circular-envelope fit; final center heights vary with the actual final body surface",
    "surfaceEnvelopeTargetClearanceMm": 0.0015,
    "fitMethod": "actual final-body triangles, ring vertices and longitudinal quarter-span samples; intentional embedded ends retained; not manufacturing certification",
    "topology": "adaptive-closed-components",
    "surface": "Three-ply normal and color detail; original stitch shape retained within sampled 0.00238 mm tolerance",
    "postHingeScope": "R15 sewing geometry unchanged; original R15 body-fit evidence is inherited, not new integrated contact certification",
    "count": 132,
    "triangleCount": 52598
  },
  "features": {
    "cap": "upper free-tail cut faces reassigned to existing edge paint",
    "backBend": "upper fair quintic cross-section translation z -8..15 mm; max 0.751093 mm; zero displacement/slope at boundaries; body/lining/edges/holes/thread aligned; attachments unchanged",
    "keepers": "local corner relief max 0.19981 mm; no global scaling; zero intersections in authored BVH fit test",
    "tangSlot": "lower tang-slot 0.90 mm wide; rounded closed end z 20.45 mm; open buckle end; lower triangle corner normals restored; unchanged tang; minimum sampled vertex gap 0.18 mm",
    "recesses": "264 inherited punctures locally curvature-refined; original rim vertices fixed; orientation guarded; no false through holes",
    "lugRoll": "exterior end bevels: UV14 own-source multi-segment rolled returns; 64-segment bore approximation, not exact legacy bore geometry",
    "textures": "dual-scale RNM normal and roughness; micro tangent handedness follows runtime normalScale sign only; GLSL r2-sign; signed TSL companion requires r187 adapter",
    "hingeTransition": {
      "scope": "central skin only; original end caps, bore and seat preserved",
      "upperUvCharts": 11,
      "lowerUvCharts": 8,
      "lowerMicroscopicIslandSimplification": "116 sampled intervals, 0.000020\u20130.0001421 mm physical arc; not exact preservation of every source UV island",
      "residuals": "Central source-cap lineage retained except separately scoped upper-right terminalReturnRamp; inherited contact pairs remain; no claim of every cap-end repair",
      "geometryGate": "all faces nondegenerate; exact cut-edge pairing; sampled UV cut residual <=2.86e-5; post-export interpolated normals normalized",
      "historicalLineageOnly": true,
      "currentEndScope": "superseded by rolledEndUV14 within declared end volumes"
    },
    "terminalReturnRamp": {
      "scope": "one upper-right connected lining/return junction; source opposite wall,bore,seat and other three meshes preserved",
      "maxCorrespondingDenseSurfaceDeviationMm": 0.000935013,
      "sampledSurfaceDeviationScope": "bidirectional sampled vertices/face-centres/edge-midpoints, not continuous analytic bound",
      "geometryBytes": 9096768,
      "decodedBudgetBytes": 9437184,
      "sourceCutPairedEdges": 422,
      "transverseCrossings": "58pairs:44identical,14same source triangle contacts after planar subdivision; no unexplained new pair",
      "uv": "explicit chart splits/shared chart vertices;float32 nozero UV area or mixed-sign charts;source-cut phase residual<=8.56e-7",
      "sourceHardwareStaticClearanceMm": {
        "case": 0.2954,
        "upperSpringbar": 0.61
      },
      "limitations": "render-quality local fillet, not CAD/manufacturing G1 continuity; tiny cap cut dihedrals retained; current source-static checks not integrated motion proof",
      "geometryBytesScope": "R17 predecessor geometry bytes; R18 total is recorded by expectedGeometry",
      "historicalLineageOnly": true,
      "currentEndScope": "superseded by rolledEndUV14 within declared end volumes"
    },
    "returnMaterialBoundary": {
      "scope": "upper-right return material boundary only; no surface displacement",
      "construction": "385 original faces subdivided by planar cuts, adding 766 triangles; existing positions preserved and new positions interpolated on source faces",
      "normals": "original vertices and outside normals unchanged; new interpolated corner normals normalized; sampled maximum difference 0.257 degrees",
      "sourceCutPairedEdges": 422,
      "sourceCutUv": "unchanged at all 422 source-cut edges",
      "uv": "destination-chart extension with local microseams on seven faces; maximum same-chart mismatch 9.54e-7 UV; float32 areas nonzero and no mixed-sign connected charts",
      "limitations": "localized material-ownership and triangulation change, not a new surface or manufacturing G1 certification; actualKTX/browser and integrated motion QA pending"
    },
    "rolledEndUV14": {
      "scope": "UL/UR/LR canonical X8.5 Y-3.5; LL X8.2 Y-3.5; four own-source patches, no finished-mesh mirroring",
      "density": "exact source attributes retained; sampled position <=.01mm, normal-component <=.02, UV <=5e-5; protected interfaces unchanged",
      "limitation": "sampled/static evidence, not manufacturing or all-pose certification; original source material island retained"
    },
    "outerChartPhaseUV15": {
      "sourceGeometrySHA256": "90015ad0a1f72b7b009ac3861069ecdff5b9488af55861a0f8a55068d2bf1136",
      "scope": "outer rolled chart B only: upper3028/lower2889 vertices",
      "change": "UV-only phase alignment; positions, normals, indices, material assignments and texture bytes unchanged",
      "limitations": "other atlas seams and original material island remain; actual mapped acceptance tracked separately"
    },
    "densityR16": {
      "scope": "rolled ends with source y greater than -5 mm; unchanged sewing and other strap surfaces",
      "tolerance": "0.008 mm attribute-aware simplifier error; independent sampled surface checks",
      "topology": "no new flipped-normal triangles, welded boundary edges or non-manifold edges"
    }
  },
  "asset": "leather-assets/r14/leather.gltf",
  "expectedGeometry": {
    "bytes": 8044710,
    "sha256": "f7e7a7638b7ac58a3d3f568cbbcc0baa989d840d9b989e10b0c72485298ed0d5",
    "bufferIndex": 0
  },
  "meshes": [
    {
      "index": 0,
      "name": "Upper strap / strap-four-end-uv15-phase",
      "primitives": [
        {
          "material": 0,
          "positionCount": 66728,
          "indexCount": 305208,
          "bounds": {
            "min": [
              -9.963666915893555,
              -48.2681999206543,
              -32.06981658935547
            ],
            "max": [
              9.963665962219238,
              0.6301339268684387,
              28.125308990478516
            ]
          }
        },
        {
          "material": 2,
          "positionCount": 7081,
          "indexCount": 34581,
          "bounds": {
            "min": [
              -9.979998588562012,
              -47.75324630737305,
              -31.306591033935547
            ],
            "max": [
              9.979998588562012,
              0.6301316022872925,
              28.125211715698242
            ]
          }
        },
        {
          "material": 1,
          "positionCount": 12849,
          "indexCount": 60519,
          "bounds": {
            "min": [
              -9.960139274597168,
              -46.72029113769531,
              -30.457202911376953
            ],
            "max": [
              9.960139274597168,
              -0.1999996304512024,
              26.894344329833984
            ]
          }
        }
      ]
    },
    {
      "index": 1,
      "name": "Upper sewing / round 0.13 mm / strap-four-end-uv15-phase",
      "primitives": [
        {
          "material": 3,
          "positionCount": 20293,
          "indexCount": 105786,
          "bounds": {
            "min": [
              -8.875805854797363,
              -48.03483963012695,
              -31.78240966796875
            ],
            "max": [
              8.866521835327148,
              -6.048745155334473,
              20.785308837890625
            ]
          }
        }
      ]
    },
    {
      "index": 2,
      "name": "Lower strap / strap-four-end-uv15-phase",
      "primitives": [
        {
          "material": 0,
          "positionCount": 42011,
          "indexCount": 189492,
          "bounds": {
            "min": [
              -9.9613037109375,
              -44.5750617980957,
              11.914806365966797
            ],
            "max": [
              9.961302757263184,
              0.6299177408218384,
              32.069923400878906
            ]
          }
        },
        {
          "material": 1,
          "positionCount": 12931,
          "indexCount": 56196,
          "bounds": {
            "min": [
              -9.960029602050781,
              -43.975067138671875,
              11.913300514221191
            ],
            "max": [
              9.960029602050781,
              -0.1999996453523636,
              30.457300186157227
            ]
          }
        },
        {
          "material": 2,
          "positionCount": 8010,
          "indexCount": 34683,
          "bounds": {
            "min": [
              -9.975000381469727,
              -44.5750617980957,
              11.913300514221191
            ],
            "max": [
              9.975000381469727,
              0.6299177408218384,
              31.30669403076172
            ]
          }
        }
      ]
    },
    {
      "index": 3,
      "name": "Lower sewing / round 0.13 mm / strap-four-end-uv15-phase",
      "primitives": [
        {
          "material": 3,
          "positionCount": 10014,
          "indexCount": 52008,
          "bounds": {
            "min": [
              -8.79917049407959,
              -39.80714797973633,
              21.243450164794922
            ],
            "max": [
              8.819087982177734,
              -6.073461055755615,
              31.78978157043457
            ]
          }
        }
      ]
    }
  ],
  "hardware": {
    "asset": "rebuild/assembly.glb",
    "expectedBytes": 25840532,
    "expectedSha256": "6ac638843c56eb4ae2f3d9ee1135facaac085ae70e2292f2b3d30f9673340039",
    "verificationScope": "Canonical assembly after caseback reconstruction and verified normal-only bake; positions, indices, UV, leather, keeper, springbar and other source identity preserved"
  },
  "generator": "marked-mesh-qa/pack.py",
  "topologyCandidate": {
    "charts": 54,
    "removedTriangles": 1504,
    "maxSampledDeviationMm": 0.007395504731940233,
    "sourceSHA256": "97377092fcfc6f5a7e934e083f71a1d5e99c9d2007a1b5c3ba38a2b6a6dc61e3"
  }
});
