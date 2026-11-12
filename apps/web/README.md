# Sauce landing page (static foundation)

A standalone Next.js 15 website inside the existing Sauce Vids repository. No changes to the Hermes plugin, capture engine, or Remotion compositor.

## Run

    cd apps/web
    npm install
    npm run dev

## Honest scope

- Desktop and mobile layout constructed from HTML/CSS.
- Bottle and sauce rendered in independent inline SVG layers: no entire-page screenshots.
- Browser product panels are **illustrative UI**, not recordings or evidence that Sauce can currently produce the exact look shown.
- Navigation works, links lead to documented sections or the GitHub repository.
- No invented customer names, logos, reviews, or business relationships.
- No fluid simulation, video upload/backend, authenticated users, or payments.

Replace the illustrative panels with synchronized real before-and-after footage from the same recorded browser journey, and replace the SVG bottle with a photoreal transparent production asset. Preserve these as independent layers.

Future animation can use the bottle, sauce stream and rim as separately controlled components. The CSS supports prefers-reduced-motion.
