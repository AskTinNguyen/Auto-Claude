/**
 * Theme constants
 * Color themes for multi-theme support with light/dark mode variants
 */

import type { ColorThemeDefinition } from '../types/settings';

// ============================================
// Color Themes
// ============================================

/**
 * Dieter Rams Design System - Multiple color themes
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
  },
  {
    id: 'beige',
    name: 'Beige',
    description: 'Warm hotel elegance with bronze gold accents',
    previewColors: {
      bg: '#FAF8F5',
      accent: '#8B6914',
      darkBg: '#2B241D',
      darkAccent: '#A87C1A'
    }
  },
  {
    id: 'cool',
    name: 'Cool Gray',
    description: 'Technical precision with slate blue accents',
    previewColors: {
      bg: '#FAFBFC',
      accent: '#2F5A8B',
      darkBg: '#1C232E',
      darkAccent: '#3D6FA3'
    }
  }
];
