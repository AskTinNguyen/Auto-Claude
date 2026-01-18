/**
 * Theme constants
 * Color themes for multi-theme support with light/dark mode variants
 */

import type { ColorThemeDefinition } from '../types/settings';

// ============================================
// Color Themes
// ============================================

/**
 * Dieter Rams Design System - Single unified theme
 * "Less but better" - Swiss precision meets timeless elegance
 */
export const COLOR_THEMES: ColorThemeDefinition[] = [
  {
    id: 'rams',
    name: 'Rams',
    description: 'Less but better - Precision and timeless elegance',
    previewColors: {
      bg: '#FAFAFA',
      accent: '#1A4D2E',
      darkBg: '#171717',
      darkAccent: '#52B788'
    }
  }
];
