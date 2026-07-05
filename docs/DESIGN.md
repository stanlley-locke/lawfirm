# Design Reference

Visual direction for the Dan Ochieng & Company Advocates website is based on **client-provided design screenshots** and the **official logo**. These assets are the primary source of truth — not third-party Figma templates.

## Primary Sources

| Asset | Path | Role |
|-------|------|------|
| **Logo (color palette)** | `static/images/logo/dan_ochieng_advocates_logo.png` | Brand colors, favicon, navbar & footer identity |
| **Design screenshots** | `static/images/design_screens/` | Layout, typography, spacing, section structure |

## Extracted Logo Palette

Sampled directly from `dan_ochieng_advocates_logo.png`:

| Token | Hex | Usage |
|-------|-----|-------|
| `--doa-navy` | `#082068` | Primary brand, headings, buttons, dark sections |
| `--doa-navy-dark` | `#001060` | Hero/footer backgrounds, deepest navy |
| `--doa-navy-light` | `#081870` | Navy mid-tone, hover states |
| `--doa-cyan` | `#00C8F8` | Accent — active nav, icons, highlights, chat widget |
| `--doa-cyan-light` | `#33D4FA` | Hover accent |
| `--doa-white` | `#FFFFFF` | Cards, forms, light surfaces |

Screenshot-derived layout surfaces (brand colors replace template browns/golds from reference mockups):

| Token | Hex | Usage |
|-------|-----|-------|
| `--doa-cream` | `#F9F7F2` | Alternate section backgrounds |
| `--doa-text` | `#333333` | Body copy on light sections |
| `--doa-footer` | `#0A0E1A` | Footer background |

## Typography

Loaded in `templates/layout.html`:

| Token | Font | Usage |
|-------|------|-------|
| `--font-heading` | Montserrat | Headings, nav links, buttons |
| `--font-body` | Open Sans | Body copy, form labels |

## Screenshot → Page Mapping

| Screenshot file | Flask template(s) | Sections implemented |
|-----------------|-------------------|----------------------|
| `homepage_hero_section.png` | `index.html` | Dark hero, centered uppercase headline, CTA |
| `homepage_after_hero_section.png` | `index.html` | Intro overlap card, practice area grid |
| `practice_areas.png` | `index.html`, `services.html` | Practice area cards, CTA banner |
| `what_our_clients_say.png` | `index.html`, `about.html` | Excellence split row, testimonials |
| `our_services_page.png` | `services.html` | Services hero, intro columns, process cards |
| `contact_us_page.png` | `contact.html` | Dark contact layout, info grid, white form |
| `our_blog.png` | `blog.html`, `index.html` | Blog grid, footer structure |
| `location_section.png` | `index.html`, `contact.html`, `layout.html` | Map embed, CTA banner, footer columns |
| `quick_inquiry.png` | `contact.html` | Consultation form styling |
| `frequently _asked_qstns.png` | `index.html`, `contact.html` | Dark FAQ accordion |
| `Screenshot 2026-07-03 215536.png` | `about.html` | Alternating image/text rows |

## Pages Without Dedicated Screenshots

These pages use the shared design system (page header hero, cream/white sections, navy CTAs, logo in layout):

| Template | Consistent styling approach |
|----------|----------------------------|
| `team.html`, `team_member.html` | Page header + practice-card / team-card grids |
| `case_studies.html`, `case_study_detail.html` | Page header + practice-card case cards |
| `service_detail.html` | Page header + content + sidebar |
| `blog_detail.html` | Page header + content card |
| `search.html` | Page header with inline search + results list |
| `appointments.html` | Page header + Calendly embed |
| `privacy.html`, `terms.html` | Page header + content card |
| `errors/404.html`, `500.html`, `403.html` | Cream error-page layout |
| `auth/login.html` | Page header + centered login card with logo |
| `chat/client_chat.html` | Navy chat header, existing SocketIO functionality |

## Shared Layout (`layout.html`)

- Light Bootstrap 5 theme (`data-bs-theme="light"`)
- Logo in navbar, footer, and favicon
- Phone number in navbar (`0729 116 086`)
- Four-column footer: Brand, Links, Find Us, Practice Areas
- Floating cyan chat widget (preserved)

## CSS Files

| File | Status |
|------|--------|
| `static/css/custom.css` | **Canonical** stylesheet with all design tokens |
| `static/css/customone.css` | Legacy duplicate — **not linked** in templates; safe to delete |

## CSS Utility Classes

| Class | Purpose |
|-------|---------|
| `section-block` | Standard vertical section padding |
| `section-cream` / `section-white` / `section-dark` | Background variants |
| `page-header` | Inner-page navy hero with title |
| `hero-section` | Full-width homepage/page hero |
| `practice-card` | White shadowed service card with READ MORE link |
| `cta-banner` / `cta-section` | Navy call-to-action bands |
| `contact-dark-section` | Dark contact page layout |
| `contact-form-card` | White form container |
| `faq-dark` | Dark accordion FAQ section |
| `link-arrow` | Uppercase “READ MORE →” link style |
| `blog-card` | Blog listing card |
| `testimonial-section` | Quote + image testimonial layout |

## Admin Panel

Admin templates (`templates/admin/*`) receive light-touch styling via shared Bootstrap overrides in `custom.css`. Logo consistency can be added to admin layout separately if needed.
