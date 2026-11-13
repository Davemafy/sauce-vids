# Sauce Blender bottle experiment

Status: technical pipeline validated on Vultr; **not an approved production asset**.

- The worker has Blender 4.5.16 LTS in ~/tools/blender-4.5.16-linux-x64.
- Actual worker container memory cap is 1 GiB, despite the VM advertising 4 GiB. The CPU render uses a single thread, 12 samples, no denoising, 560x740.
- The supplied legacy Tripo GLB exists as a ChatGPT conversation upload but was **not transferred to the isolated VM**. Neither experiment render used that source asset.
- A procedural proxy was generated to validate the script, physically separate cap, label object, materials, lighting, transparent output, and editable scene.
- The procedural proxy **does not meet the approved premium Sauce reference**. It must not replace the existing website bottle.
- The source import path is provided but not visually verified against the H2.5 mesh.

Run in the VM workspace:

    cd sauce-vids
    mkdir -p assets/sauce-bottle
    export SAUCE_RENDER_DIR="$PWD/assets/sauce-bottle"
    ~/tools/blender-4.5.16-linux-x64/blender -b -t 1 --python scripts/render_sauce.py -- /path/to/ketchup-bottle.glb

Without the optional GLB path, the script renders a procedural fallback. Output: studio and hero PNG images plus an editable .blend scene.

Next actual production work: transfer the original GLB to the isolated VM, inspect surface issues at 1:1, fix original topology and UV labeling, render the approved inverted pose, and only then replace the static SVG in apps/web.
