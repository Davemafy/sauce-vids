# Sauce bottle — Blender render experiment

## Status

This is a **procedural Blender reconstruction** of the Sauce squeeze bottle based on the approved visual direction and the Tripo H2.5 reference screenshots. **It is not a cleaned or imported copy of the user's H2.5 GLB.** The chat-uploaded binary is not directly mounted in the isolated Vultr worker.

This asset is a **candidate**, not the approved photorealistic master. The existing website hero is not automatically replaced.

## Infrastructure actually used

- DevMCP persistent Vultr worker, isolated workspace
- Blender 4.5.3 LTS running headlessly with Cycles on CPU
- 2 vCPUs / 4 GB RAM; NVIDIA GPU not present
- 600 × 750 transparent test render, 32 samples (~21 seconds)
- Rendered asset: \`apps/web/public/assets/sauce-bottle-candidate.webp\` (transparent, approx 24 KB)
- UV-printed label art: \`scripts/sauce-label.svg\`
- Reproducible build: \`scripts/render_bottle_blender.py\`
- Blender \`.blend\` and GLB exports retained in the persistent worker's \`sauce-vids/renders/\` directory.

## Rebuild the candidate

From the repository root, with Blender 4.5+ and FFmpeg available:

\`\`\`sh
mkdir -p renders
ffmpeg -hide_banner -loglevel error -y -i scripts/sauce-label.svg -frames:v 1 renders/sauce-label.png
SAUCE_WIDTH=1200 SAUCE_HEIGHT=1500 SAUCE_SAMPLES=64 SAUCE_RENDER_OUT=./renders/sauce-bottle.png blender -b -t 2 --python scripts/render_bottle_blender.py
ffmpeg -hide_banner -loglevel error -y -i renders/sauce-bottle.png -c:v libwebp -quality 90 -compression_level 6 -pix_fmt yuva420p renders/sauce-bottle.webp
\`\`\`

The script saves an editable .blend beside the PNG. To export an editable scene/GLB, open the .blend in Blender and export glTF 2.0 Binary.

## Known gaps

- The procedural geometry does not reproduce the detailed Tripo H2.5 mesh.
- Cap hinge is stylized, not mechanically accurate.
- Lighting, curvature and product-specular response require additional visual-reference comparisons.
- Sauce flow and video-frame interaction are independent assets and are not included here.
- The actual uploaded H2.5 GLB still needs an authorized transfer into the worker before we can repair that exact mesh.
