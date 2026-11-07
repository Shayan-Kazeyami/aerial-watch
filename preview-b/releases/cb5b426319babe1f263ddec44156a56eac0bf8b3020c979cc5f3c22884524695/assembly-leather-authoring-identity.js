// Generated from final geometry bytes + explicit authoring spec. Regenerate after EVERY asset edit.
export const AUTHORED_LEATHER_IDENTITY=Object.freeze({
  "schemaVersion": 1,
  "id": "strap-hinge-skin-sourcecharts-r16-candidate",
  "status": "unpublished integrated hinge candidate; full viewer acceptance pending",
  "legacySelection": "craft14",
  "lineage": "R15 thread/recess/strap design plus locally rebuilt upper and lower roll-to-strap skins; inherited R14 textures/load path",
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
    "lugRoll": "exterior end bevels only: springbar 0.10 mm, buckle 0.08 mm; original bore and springbar attachment preserved",
    "textures": "dual-scale RNM normal and roughness; micro tangent handedness follows runtime normalScale sign only; GLSL r2-sign; signed TSL companion requires r187 adapter",
    "hingeTransition": {
      "scope": "central skin only; original end caps, bore and seat preserved",
      "upperUvCharts": 11,
      "lowerUvCharts": 8,
      "lowerMicroscopicIslandSimplification": "116 sampled intervals, 0.000020–0.0001421 mm physical arc; not exact preservation of every source UV island",
      "residuals": "source cap pinch and inherited crossings retained; no new transverse pair in cropped welded SAT checks",
      "geometryGate": "all faces nondegenerate; exact cut-edge pairing; sampled UV cut residual <=2.86e-5; post-export interpolated normals normalized"
    }
  },
  "asset": "leather-assets/r14/leather.gltf",
  "expectedGeometry": {
    "bytes": 8814096,
    "sha256": "d473da297e6dd6565c8c98b3b3e36602f6ed7703c60e51a0205d2ac070825fb0",
    "bufferIndex": 0
  },
  "meshes": [
    {
      "index": 0,
      "name": "Upper strap / strap-hinge-skin-sourcecharts-r16-candidate",
      "primitives": [
        {
          "material": 0,
          "positionCount": 67875,
          "indexCount": 309120,
          "bounds": {
            "min": [
              -9.99984359741211,
              -48.2681999206543,
              -32.06981658935547
            ],
            "max": [
              9.999845504760742,
              0.630427896976471,
              28.125308990478516
            ]
          }
        },
        {
          "material": 2,
          "positionCount": 4766,
          "indexCount": 17940,
          "bounds": {
            "min": [
              -9.999983787536621,
              -47.75324630737305,
              -31.306591033935547
            ],
            "max": [
              9.999983787536621,
              0.630171000957489,
              28.125211715698242
            ]
          }
        },
        {
          "material": 1,
          "positionCount": 14218,
          "indexCount": 68850,
          "bounds": {
            "min": [
              -9.974851608276367,
              -46.72029113769531,
              -30.457202911376953
            ],
            "max": [
              9.974851608276367,
              -0.19944237172603607,
              26.894344329833984
            ]
          }
        }
      ]
    },
    {
      "index": 1,
      "name": "Upper sewing / round 0.13 mm / strap-hinge-skin-sourcecharts-r16-candidate",
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
      "name": "Lower strap / strap-hinge-skin-sourcecharts-r16-candidate",
      "primitives": [
        {
          "material": 0,
          "positionCount": 42791,
          "indexCount": 190890,
          "bounds": {
            "min": [
              -9.999964714050293,
              -44.5750617980957,
              11.914806365966797
            ],
            "max": [
              9.999966621398926,
              0.6300918459892273,
              32.069923400878906
            ]
          }
        },
        {
          "material": 1,
          "positionCount": 15260,
          "indexCount": 69009,
          "bounds": {
            "min": [
              -9.974967002868652,
              -43.975067138671875,
              11.913300514221191
            ],
            "max": [
              9.974967002868652,
              -0.1998797506093979,
              30.457300186157227
            ]
          }
        },
        {
          "material": 2,
          "positionCount": 5950,
          "indexCount": 19482,
          "bounds": {
            "min": [
              -9.999993324279785,
              -44.5750617980957,
              11.913300514221191
            ],
            "max": [
              9.999993324279785,
              0.6300367712974548,
              31.30669403076172
            ]
          }
        }
      ]
    },
    {
      "index": 3,
      "name": "Lower sewing / round 0.13 mm / strap-hinge-skin-sourcecharts-r16-candidate",
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
    "expectedBytes": 26126756,
    "expectedSha256": "04335bab9e05f1610984ceeee355a80e06277ed1f3d7980355a9f8a2146fe6bf",
    "verificationScope": "expected source identity only; not verified by leather-buffer loader"
  },
  "generator": "scripts/generate-leather-identity.mjs"
});
