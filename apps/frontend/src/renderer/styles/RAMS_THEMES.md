# Rams Design System - Color Schemes

This directory contains the Rams design system with four distinct color schemes, all following Dieter Rams' principle of "Less but better" and maintaining WCAG 2.1 AA accessibility compliance.

## Design Philosophy

**Core Principles:**
- **Less but better** - Minimal, purposeful design
- **Swiss precision** - Tight typography and 4px spacing system
- **Timeless elegance** - Classic, enduring aesthetics
- **High accessibility** - WCAG 2.1 AA compliant contrast ratios

**Shared Design Language:**
- Typography: SF Pro Display / Helvetica Neue
- Monospace: SF Mono / Menlo
- Spacing: Precise 4px incremental system
- Shadows: Subtle and refined
- Borders: Minimal 1px with minimal radius (2-6px)
- Transitions: Fast (100ms) and normal (200ms) easing

---

## Available Themes

### 1. Default (Light Mode) - `rams-design-system.css`

**Primary Palette:**
- Background: Pure white (#FFFFFF)
- Grays: Refined neutrals (#FAFAFA → #171717)
- Accent: Deep Forest Green (#1A4D2E)

**Use Cases:**
- Default light mode
- Professional documentation
- Clean, minimal interfaces

**Accent Philosophy:** Deep forest green inspired by hotel elegance and natural luxury.

---

### 2. Dark Mode - `rams-dark.css`

**Primary Palette:**
- Background: Deep black (#0A0A0A)
- Grays: Inverted scale (blacks → soft whites)
- Accent: Bright Forest Green (#52B788)

**Use Cases:**
- Night mode / reduced eye strain
- Focus mode for coding
- Modern, high-contrast interfaces

**Key Features:**
- Higher contrast for readability
- Brighter accent for visibility
- Enhanced shadows (30-60% opacity)
- Inverted grayscale maintains Rams precision

**Activation:**
```html
<html data-theme="dark">
```

---

### 3. Beige Mode - `rams-beige.css`

**Primary Palette:**
- Background: Warm cream (#FAF8F5)
- Grays: Warm beige tones (#F5F2ED → #2B241D)
- Accent: Bronze Gold (#8B6914)

**Use Cases:**
- Luxury/hotel applications
- Warm, elegant interfaces
- Reading-focused experiences
- Print-inspired digital design

**Accent Philosophy:** Bronze gold evokes Intercontinental Hotel sophistication and timeless luxury.

**Key Features:**
- Warm, paper-like tones
- Reduced blue light (easier on eyes)
- Hotel lobby elegance
- Sophisticated, classic feel

**Activation:**
```html
<html data-theme="beige">
```

---

### 4. Cool Gray Mode - `rams-cool.css`

**Primary Palette:**
- Background: Cool white (#FAFBFC)
- Grays: Blue-gray tones (#F5F7FA → #1C232E)
- Accent: Slate Blue (#2F5A8B)

**Use Cases:**
- Technical/engineering interfaces
- Data visualization dashboards
- Clinical/medical applications
- Swiss modernism aesthetic

**Accent Philosophy:** Slate blue represents technical precision and Braun design heritage.

**Key Features:**
- Cool, clinical tones
- Blue-gray palette for focus
- Technical precision aesthetic
- Swiss modernism inspired

**Activation:**
```html
<html data-theme="cool">
```

---

## Usage

### Basic Integration

```html
<!-- Include base design system (always required) -->
<link rel="stylesheet" href="./styles/rams-design-system.css">

<!-- Include theme variants (only load what you need) -->
<link rel="stylesheet" href="./styles/rams-dark.css">
<link rel="stylesheet" href="./styles/rams-beige.css">
<link rel="stylesheet" href="./styles/rams-cool.css">
```

### Theme Switching

```javascript
// Set theme via data attribute
document.documentElement.setAttribute('data-theme', 'dark');   // Dark mode
document.documentElement.setAttribute('data-theme', 'beige');  // Beige mode
document.documentElement.setAttribute('data-theme', 'cool');   // Cool gray mode
document.documentElement.removeAttribute('data-theme');        // Default light mode
```

### Prefers Color Scheme

```javascript
// Auto-detect user preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
if (prefersDark) {
  document.documentElement.setAttribute('data-theme', 'dark');
}
```

---

## Accessibility Compliance

All themes maintain **WCAG 2.1 AA** compliance:

| Element | Contrast Ratio | Standard |
|---------|----------------|----------|
| Body text | ≥ 4.5:1 | AA (Normal) |
| Large text (18pt+) | ≥ 3:1 | AA (Large) |
| UI Components | ≥ 3:1 | AA (Graphics) |
| Focus indicators | ≥ 3:1 | AA (Non-text) |

**Dark Mode Enhancements:**
- Higher shadow opacity (30-60% vs 5-10%)
- Brighter accent colors for visibility
- Inverted text contrast (light on dark)

**Alert Boxes:**
- Error: Red with 7:1+ contrast
- Warning: Orange with 7:1+ contrast
- Success: Green with 7:1+ contrast
- Info: Blue with 7:1+ contrast

---

## Color Variable Reference

### Using Theme Variables

All themes override the same CSS variables, ensuring consistent API:

```css
/* These work across all themes */
var(--rams-accent)          /* Primary brand color */
var(--rams-accent-light)    /* Lighter accent variant */
var(--rams-accent-dark)     /* Darker accent variant */

var(--rams-gray-50)         /* Lightest gray */
var(--rams-gray-500)        /* Mid gray */
var(--rams-gray-900)        /* Darkest gray */

var(--rams-success)         /* Success state */
var(--rams-warning)         /* Warning state */
var(--rams-error)           /* Error state */
var(--rams-info)            /* Info state */
```

### Creating Custom Components

```css
.my-custom-card {
  background: var(--rams-white);
  color: var(--rams-gray-900);
  border: var(--rams-border-width) solid var(--rams-border-color);
  padding: var(--rams-space-4);
  border-radius: var(--rams-radius-md);
}

.my-custom-card:hover {
  border-color: var(--rams-accent);
  box-shadow: var(--rams-shadow-sm);
}
```

This approach ensures your components automatically adapt to theme changes.

---

## Class Naming Convention

All Rams design system classes use the `.rams-` prefix:

**Layout:**
- `.rams-page` - Root container
- `.rams-sidebar` - Sidebar navigation
- `.rams-main` - Main content area
- `.rams-topbar` - Top navigation bar

**Typography:**
- `.rams-h1`, `.rams-h2`, `.rams-h3` - Headings
- `.rams-text`, `.rams-text-sm` - Body text
- `.rams-code-inline` - Inline code

**Components:**
- `.rams-btn`, `.rams-btn-primary` - Buttons
- `.rams-alert-error`, `.rams-alert-success` - Alerts
- `.rams-card`, `.rams-feature-card` - Cards
- `.rams-nav-link` - Navigation links

**Utilities:**
- `.rams-text-center` - Center alignment
- `.rams-section-gray` - Gray background section

---

## Theme Comparison

| Aspect | Default | Dark | Beige | Cool |
|--------|---------|------|-------|------|
| **Mood** | Clean & neutral | Modern & focused | Warm & elegant | Technical & precise |
| **Background** | Pure white | Deep black | Warm cream | Cool white |
| **Accent Hue** | Green | Green | Bronze | Blue |
| **Best For** | General use | Night work | Luxury brands | Engineering |
| **Eye Strain** | Neutral | Low (dark) | Low (warm) | Neutral |
| **Formality** | Professional | Modern | Luxurious | Clinical |

---

## Migration Guide

### From Legacy CSS

If migrating from existing styles:

1. **Import base system first:**
   ```html
   <link rel="stylesheet" href="./styles/rams-design-system.css">
   ```

2. **Replace custom colors with Rams variables:**
   ```css
   /* Before */
   background: #f5f5f5;
   color: #333;

   /* After */
   background: var(--rams-gray-100);
   color: var(--rams-gray-900);
   ```

3. **Use Rams components:**
   ```html
   <!-- Before -->
   <div class="custom-card">...</div>

   <!-- After -->
   <div class="rams-feature-card">...</div>
   ```

4. **Add theme switching:**
   ```javascript
   // Add theme toggle button
   const toggleTheme = () => {
     const current = document.documentElement.getAttribute('data-theme');
     const next = current === 'dark' ? null : 'dark';
     document.documentElement.setAttribute('data-theme', next || '');
   };
   ```

---

## Performance Considerations

- **Load only what you need:** If you only use default + dark, don't load beige/cool CSS
- **CSS Custom Properties:** All themes use CSS variables (no JavaScript needed for colors)
- **File sizes:**
  - Base system: ~45KB (uncompressed)
  - Each theme variant: ~8KB (uncompressed)
  - Gzipped total: ~12KB for all themes

---

## Customization

### Creating a New Theme

1. Copy an existing theme CSS file
2. Update the `:root[data-theme="your-name"]` selector
3. Override color variables:
   ```css
   :root[data-theme="your-name"] {
     --rams-accent: #YOUR_COLOR;
     --rams-gray-50: #YOUR_LIGHT;
     --rams-gray-900: #YOUR_DARK;
     /* ... */
   }
   ```
4. Test accessibility with contrast checkers
5. Activate: `data-theme="your-name"`

### Extending Components

```css
/* Add to your custom CSS file */
.rams-custom-component {
  /* Use Rams variables */
  background: var(--rams-gray-50);
  border: var(--rams-border-width) solid var(--rams-border-color);
  padding: var(--rams-space-4);
  border-radius: var(--rams-radius-md);
}
```

---

## Browser Support

- **Modern browsers:** Full support (Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+)
- **CSS Custom Properties:** Required (no fallbacks for IE11)
- **CSS Grid/Flexbox:** Used throughout
- **Reduced Motion:** Respects `prefers-reduced-motion` for accessibility

---

## Credits

**Design Philosophy:**
- Dieter Rams (10 Principles of Good Design)
- Swiss Design Movement
- Braun Industrial Design

**Color Inspiration:**
- Default: Forest green + neutral grays
- Dark: OLED-optimized blacks
- Beige: Intercontinental Hotel interiors
- Cool: Swiss modernism + Braun aesthetics

---

## License

This design system is part of Auto-Claude. See the main project license for terms.

---

## Questions?

For issues or suggestions, please file an issue in the Auto-Claude repository.
