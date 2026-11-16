# FlowPilot AI — Blue Liquid Glass / Fluid Glass Design System

This document specifies the global design system tokens, surface physics, liquid glass primitives, micro-interactions, and accessibility standards powering FlowPilot AI.

---

## 1. Core Visual Philosophy

FlowPilot AI's visual identity combines:
- **Deep Midnight-Blue Substrates**: Optical depth anchored by `#080F20` and `#0C1629`.
- **Liquid-Glass Translucency**: Layered semi-transparent backdrops (`#111E35`/`#172743` with `backdrop-filter: blur(16px)` to `blur(24px)`).
- **Subtle Prismatic Edge Lighting**: Inset top highlights (`inset 0 1px 1px rgba(255, 255, 255, 0.12)`) and translucent cyan/electric-blue borders (`rgba(67, 139, 255, 0.2)`).
- **Electric Blue Accents & Soft Cyan Highlights**: Active indicators and brand focal points (`#287BFA`, `#438BFF`, `#53D7F5`).
- **Restrained Motion & Optical Ergonomics**: Respects `prefers-reduced-motion` and avoids CPU/GPU intensive canvas calculations.

---

## 2. Centralized Design Tokens

| Token Name | Hex / Value | Semantic Role |
| :--- | :--- | :--- |
| **`--background`** | `#080F20` | Root canvas / deep substrate |
| **`--secondary-bg`** | `#0C1629` | Topbar, sidebar base, inner panels |
| **`--surface`** | `#111E35` | Standard liquid glass card & panel background |
| **`--elevated`** | `#172743` | Modals, dropdowns, hovered elevated cards |
| **`--primary-blue`** | `#287BFA` | Primary buttons, brand gradient root |
| **`--electric-blue`** | `#438BFF` | Active borders, running status, focal glow |
| **`--cyan-accent`** | `#53D7F5` | Secondary accent, metrics, edge highlights |
| **`--soft-blue`** | `#8DBBFF` | Subdued pills, links, secondary badges |
| **`--success`** | `#28C995` | Emerald execution success, connected state |
| **`--warning`** | `#F2B65D` | Amber pending approval, conditional branch |
| **`--error`** | `#F16B7A` | Coral failure, rejection, error toast |
| **`--text-primary`** | `#F1F6FF` | High-contrast body, titles, headings |
| **`--text-secondary`**| `#A3B4CF` | Subtitles, labels, metadata |
| **`--text-muted`** | `#7285A5` | Footers, timestamps, disabled states |
| **`--border-glass`** | `rgba(67, 139, 255, 0.20)` | Outer border for standard glass cards |
| **`--border-glass-elevated`**| `rgba(83, 215, 245, 0.35)` | Outer border for active/focused glass |

---

## 3. Liquid Glass UI Primitives

All primitives are defined centrally in `frontend/src/app/globals.css` and integrated into Tailwind CSS v4 `@theme inline`:

### Glass Card (`.glass-card`)
```css
.glass-card {
  background: rgba(17, 30, 53, 0.72);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(67, 139, 255, 0.20);
  box-shadow: 
    inset 0 1px 1px rgba(255, 255, 255, 0.08),
    0 8px 32px rgba(4, 9, 20, 0.37);
  border-radius: 0.875rem;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.glass-card:hover {
  background: rgba(23, 39, 67, 0.82);
  border-color: rgba(83, 215, 245, 0.38);
  box-shadow: 
    inset 0 1px 1px rgba(255, 255, 255, 0.14),
    0 12px 36px rgba(40, 123, 250, 0.16);
  transform: translateY(-2px);
}
```

### Glass Panel (`.glass-panel`)
Used for sidebars, top headers, and fixed floating navigation.
```css
.glass-panel {
  background: rgba(12, 22, 41, 0.80);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(67, 139, 255, 0.15);
  box-shadow: 0 12px 40px rgba(4, 9, 20, 0.45);
}
```

### Glass Buttons
- **Primary (`.glass-btn-primary`)**:
  `background: linear-gradient(135deg, #287BFA 0%, #438BFF 100%)` with electric-blue glow and inner reflection.
- **Secondary (`.glass-btn-secondary`)**:
  `background: rgba(23, 39, 67, 0.6)` with `border: 1px solid rgba(67, 139, 255, 0.25)`.

### Glass Inputs (`.glass-input`)
- `background: rgba(12, 22, 41, 0.65)`
- `border: 1px solid rgba(67, 139, 255, 0.22)`
- Focus state: `ring-2 ring-[#438BFF] border-[#53D7F5]` with soft cyan outer illumination.

---

## 4. Workflow Studio & Canvas Integration

- **Node Surfaces**: `.flow-node` uses layered glass with `rgba(17, 30, 53, 0.90)` and subtle cyan header dividers.
- **Selection Glow**: Selected node activates `ring-2 ring-[#438BFF] border-[#53D7F5] shadow-[0_0_24px_rgba(67,139,255,0.45)]`.
- **Handles & Ports**:
  - Standard In/Out: `#438BFF` with `#080F20` outer rim.
  - Success/Condition True: Emerald `#28C995`.
  - Failure/Condition False: Coral `#F16B7A`.
- **Canvas Edge Routing**: React Flow edges rendered with stroke `#438BFF`, `strokeWidth: 2`, and smooth bezier curvature.

---

## 5. Accessibility & Motion Preferences

1. **High Text Contrast**:
   - Primary text (`#F1F6FF`) on midnight surface (`#111E35`) has a contrast ratio of **14.8:1** (far exceeding WCAG AAA minimum 7:1).
   - Secondary text (`#A3B4CF`) has an **8.2:1** contrast ratio.
2. **Reduced Motion**:
   - Fully supports `@media (prefers-reduced-motion: reduce)`:
   - Disables all transforms, hover translations, and pulse loops.
3. **Backdrop-Filter Fallback**:
   - `@supports not (backdrop-filter: blur(10px))` applies high-opacity solid surfaces (`rgba(17, 30, 53, 0.98)`).
