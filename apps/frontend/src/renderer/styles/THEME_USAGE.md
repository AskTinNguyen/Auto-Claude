# Theme Usage Guide - Auto Claude

The Electron app now supports **four color themes** following Dieter Rams design principles:

## Available Themes

| Theme | Class Name | Description | Best For |
|-------|------------|-------------|----------|
| **Light** | `:root` (default) | Clean white with forest green | General use, professional |
| **Dark** | `.dark` | Deep blacks with bright green | Night mode, reduced eye strain |
| **Beige** | `.beige` | Warm cream with bronze gold | Luxury feel, reduced blue light |
| **Cool** | `.cool` | Blue-gray with slate blue | Technical precision, data focus |

## How to Apply Themes

### Option 1: Via className (React)

```tsx
// In your App.tsx or root component
function App() {
  const [theme, setTheme] = useState<'dark' | 'beige' | 'cool' | null>(null);

  return (
    <div className={theme || ''}>
      {/* Your app content */}
    </div>
  );
}
```

### Option 2: Via body element

```tsx
// Change theme dynamically
useEffect(() => {
  // Remove all theme classes
  document.body.classList.remove('dark', 'beige', 'cool');

  // Add selected theme (or none for light mode)
  if (theme) {
    document.body.classList.add(theme);
  }
}, [theme]);
```

### Option 3: Via document.documentElement

```tsx
// For global theme switching
const setTheme = (themeName: 'dark' | 'beige' | 'cool' | 'light') => {
  const root = document.documentElement;
  root.classList.remove('dark', 'beige', 'cool');

  if (themeName !== 'light') {
    root.classList.add(themeName);
  }
};
```

## Integration with Existing Components

All existing components will automatically adapt because they use CSS variables:

```tsx
// This button works with all themes automatically
<button className="bg-primary text-primary-foreground">
  Click me
</button>

// Cards adapt their colors
<div className="bg-card text-card-foreground border border-border">
  Content adapts to theme
</div>
```

## Theme Persistence

To save user's theme preference:

```tsx
// Save to localStorage
const saveTheme = (theme: string) => {
  localStorage.setItem('theme', theme);
  applyTheme(theme);
};

// Load on app start
useEffect(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    applyTheme(savedTheme);
  }
}, []);
```

## Settings UI Example

Create a theme selector in your settings:

```tsx
import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark' | 'beige' | 'cool';

function ThemeSelector() {
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    // Apply theme to body
    document.body.classList.remove('dark', 'beige', 'cool');
    if (theme !== 'light') {
      document.body.classList.add(theme);
    }

    // Save preference
    localStorage.setItem('theme', theme);
  }, [theme]);

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Color Theme</label>
      <select
        value={theme}
        onChange={(e) => setTheme(e.target.value as Theme)}
        className="w-full p-2 rounded border border-border bg-card"
      >
        <option value="light">Light (Default)</option>
        <option value="dark">Dark</option>
        <option value="beige">Beige (Warm)</option>
        <option value="cool">Cool Gray</option>
      </select>
    </div>
  );
}
```

## Theme Preview Cards

Show visual previews of each theme:

```tsx
function ThemePreview({ themeName }: { themeName: Theme }) {
  return (
    <div className={themeName}>
      <div className="p-4 bg-background border border-border rounded">
        <div className="bg-card p-3 rounded border border-border">
          <div className="text-sm font-medium text-foreground">
            {themeName}
          </div>
          <div className="flex gap-2 mt-2">
            <div className="w-8 h-8 rounded bg-primary" />
            <div className="w-8 h-8 rounded bg-secondary" />
            <div className="w-8 h-8 rounded bg-accent" />
          </div>
        </div>
      </div>
    </div>
  );
}
```

## CSS Variables Available

All themes override these variables:

```css
--background          /* Main background color */
--foreground          /* Main text color */
--card               /* Card background */
--card-foreground    /* Card text */
--primary            /* Brand/accent color */
--primary-foreground /* Text on primary */
--secondary          /* Secondary surfaces */
--muted              /* Muted backgrounds */
--muted-foreground   /* Muted text */
--border             /* Border color */
--success, --warning, --error, --info  /* Semantic colors */
--shadow-sm, --shadow-md, --shadow-lg  /* Shadows */
```

## Auto Dark Mode Detection

Respect system preferences:

```tsx
useEffect(() => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  const handleChange = (e: MediaQueryListEvent) => {
    if (!localStorage.getItem('theme')) {
      // Only auto-switch if user hasn't set a preference
      setTheme(e.matches ? 'dark' : 'light');
    }
  };

  mediaQuery.addEventListener('change', handleChange);
  return () => mediaQuery.removeEventListener('change', handleChange);
}, []);
```

## Testing Themes

To test all themes quickly:

```tsx
// Cycle through themes for testing
const themes: Theme[] = ['light', 'dark', 'beige', 'cool'];
let index = 0;

function cycleTheme() {
  index = (index + 1) % themes.length;
  setTheme(themes[index]);
}

// Add keyboard shortcut (dev mode)
useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if (e.key === 'T' && e.shiftKey && e.metaKey) {
      cycleTheme();
    }
  };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, []);
```

## Important Notes

1. **No Breaking Changes**: All existing components work without modification
2. **CSS Variables**: Themes work via CSS custom properties (`:root` selector)
3. **Performance**: Theme switching is instant (no re-render needed)
4. **Accessibility**: All themes maintain WCAG 2.1 AA contrast ratios
5. **Sizing Preserved**: Only colors change - all spacing, fonts, and layouts stay the same

## Next Steps

1. Add theme selector to Settings page
2. Persist user preference in localStorage or user settings
3. Optional: Add theme preview cards in settings
4. Optional: Support system dark mode auto-detection
5. Optional: Add smooth transitions between themes

## Example Full Implementation

See `/apps/frontend/src/renderer/components/settings/ThemeSettings.tsx` (to be created) for a complete implementation example.
