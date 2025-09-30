# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Fridge2Fork Admin Web** - Admin dashboard for managing the Fridge2Fork ("오늘의냉장고") service. This is the frontend web application built with Next.js 15, TypeScript, and Tailwind CSS.

**Related Backend**: The admin API backend is located at `/home/woohaen88/woohalabs/fridge2fork/admin/backend`

## Development Commands

### Essential Commands
```bash
npm run dev          # Start development server with Turbopack (http://localhost:3000)
npm run build        # Build for production with Turbopack
npm start            # Start production server
npm run lint         # Run ESLint
```

### Working with the Backend
The backend API is in a separate directory (`../backend`). When working on full-stack features, you'll need to coordinate between both projects.

## Architecture & Design System

### Theme System (MANDATORY)

This project uses a **Linear-inspired theme system** with strict requirements:

**Components Location** (referenced but not yet created):
- `lib/theme.ts` - Theme system configuration
- `lib/utils.ts` - Utility functions including `cn()` for class merging
- `components/ui/` - Reusable UI components (Button, Card, Carousel, Input)
- `components/layout/` - Layout components (Navbar, Footer, Container, Grid, Hero)

**Color System**:
- Primary Background: `#080a0a` (--bg-primary)
- Secondary Background: `#0c0d0e` (--bg-secondary)
- Card Background: `#232328` (--bg-card)
- Primary Text: `#f7f8f8` (--text-primary)
- Secondary Text: `#8a8f98` (--text-secondary)
- Accent Color: `#FFA451` (--accent-primary)

**Typography**:
- Primary Font: Inter Variable, SF Pro Display, system fonts
- Mono Font: SF Mono, Monaco, system mono fonts
- Font Weights: 300, 400, 500, 510, 700

**Spacing Scale**: 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px, 64px, 80px, 96px, 128px
**Border Radius**: 4px, 8px, 12px, 16px, 24px, 9999px

### Reference Themes

The `reference/` directory contains theme specifications:
- `admin-theme.json` - Contains Plane and Vercel theme specifications as reference
- `admin-theme.css` - CSS reference for theme implementation

These are **reference materials** - the actual implementation should use Tailwind CSS with CSS variables.

## Component Development Rules

### MANDATORY Requirements

1. **All components MUST use TypeScript** with proper interface definitions
2. **Use `React.forwardRef`** for components that may need ref forwarding
3. **Set `displayName`** on all components
4. **Document with JSDoc** comments
5. **Use Tailwind CSS** - NO inline styles, NO CSS-in-JS libraries (styled-components, emotion)
6. **Use `cn()` utility** for className merging (from `lib/utils.ts`)
7. **Follow the theme system** - Use CSS variables, no hardcoded colors/spacing

### Component Patterns

**Example Button Component Structure**:
```typescript
import { cn } from "@/lib/utils";

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  // ... other props
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', className, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(/* variant & size classes */, className)}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
```

### Styling Constraints

**NEVER use**:
- Inline styles (`style` attribute)
- CSS-in-JS libraries
- Other UI libraries (Material-UI, Ant Design, etc.)
- Custom CSS files (except modifying `globals.css`)
- Hardcoded color values or spacing values

### Accessibility Requirements

- All interactive elements need `aria-label` or `aria-labelledby`
- Support keyboard navigation
- Maintain WCAG 2.1 AA color contrast ratios
- Use semantic HTML (`button`, `nav`, `main`, `section`)
- Follow proper heading hierarchy (h1 → h2 → h3)

## Current State

**Status**: Fresh Next.js 15 project with basic setup

**Completed**:
- Next.js 15 with TypeScript configuration
- Tailwind CSS v4 setup
- ESLint configuration
- Basic app structure (`src/app/`)
- Geist font integration

**Missing** (referenced in rules but not yet implemented):
- `lib/theme.ts` and `lib/utils.ts`
- UI components (`components/ui/`)
- Layout components (`components/layout/`)

When creating these, **strictly follow** the patterns defined in `.cursor/rules/.cursorrules.mdc`.

## Path Aliases

TypeScript is configured with `@/*` alias pointing to `./src/*`:
```typescript
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
```

## Performance & Optimization

- Use `React.memo` for components with expensive renders
- Apply `useCallback` and `useMemo` appropriately
- Use Next.js `Image` component for all images
- Implement code splitting with dynamic imports
- Avoid unnecessary library imports (tree-shaking)

## Testing Guidelines

When implementing tests:
- Write unit tests for all components
- Test user interactions
- Include accessibility tests
- Implement E2E tests for critical user flows
- Test responsive design across breakpoints

## Project Context

This is part of a larger **Fridge2Fork** ("오늘의냉장고") system:
- Purpose: "From fridge to fork" - managing food inventory and recipes
- This web app: Admin dashboard for managing the service
- Backend API: FastAPI application in `../backend/`
- The design guide mentioned in `myrequest.txt` suggests following specific design patterns