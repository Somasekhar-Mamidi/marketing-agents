# DEEP PLAN 1: Complete shadcn/ui Frontend Implementation

## Executive Summary
Transform the existing basic Next.js frontend into a professional, polished UI using shadcn/ui components with full dark mode support, responsive design, and smooth animations.

## Timeline: 2-3 weeks

---

## Phase 1: Setup & Configuration (Days 1-2)

### 1.1 Environment Setup
- [ ] Backup existing frontend code
- [ ] Verify Node.js 18+ installation
- [ ] Check current build status
- [ ] Document current dependencies

### 1.2 Initialize shadcn/ui
- [ ] Run `npx shadcn@latest init`
  - Select TypeScript: Yes
  - Select base color: Slate
  - Enable CSS variables: Yes
- [ ] Verify `components.json` created
- [ ] Verify `lib/utils.ts` created

### 1.3 Install Core Dependencies
```bash
# shadcn components
npx shadcn@latest add button card input badge progress tabs
npx shadcn@latest add separator scroll-area skeleton sonner
npx shadcn@latest add select label dialog dropdown-menu
npx shadcn@latest add table tooltip avatar command
npx shadcn@latest add sheet breadcrumb navigation-menu

# Animation & utilities
npm install framer-motion lucide-react date-fns
npm install recharts  # For analytics charts
npm install @tanstack/react-table  # For data tables
```

### 1.4 Configuration Files
- [ ] Update `tailwind.config.ts`
  - Add custom colors (agent colors, tier colors)
  - Add custom animations
  - Configure dark mode
- [ ] Update `app/globals.css`
  - Add CSS variables for theming
  - Add custom scrollbar styles
  - Add animation keyframes
- [ ] Update `app/layout.tsx`
  - Add ThemeProvider
  - Add Toaster for notifications
  - Configure fonts

### 1.5 Verify Setup
- [ ] Run `npm run dev`
- [ ] Verify no build errors
- [ ] Test dark mode toggle
- [ ] Confirm all components import correctly

**Deliverable:** Working shadcn/ui foundation with all dependencies installed

---

## Phase 2: Core Components (Days 3-7)

### 2.1 Layout Components
- [ ] `components/layout/sidebar.tsx`
  - Navigation menu
  - Logo placement
  - Collapsible on mobile
  - Recent pipelines section
- [ ] `components/layout/header.tsx`
  - Breadcrumb navigation
  - Theme toggle
  - User menu
  - Notifications bell
- [ ] `components/layout/container.tsx`
  - Responsive container wrapper
  - Consistent padding/margins

### 2.2 Agent Visualization Components
- [ ] `components/agent/agent-card.tsx`
  - Individual agent display
  - Progress indicator
  - Status badge (pending/running/completed/failed)
  - Icon and color coding
  - Animation on status change
- [ ] `components/agent/agent-grid.tsx`
  - 2x3 grid layout for 6 agents
  - Responsive (stack on mobile)
  - Connection lines between agents
  - Overall progress indicator
- [ ] `components/agent/agent-status.tsx`
  - Status icons and colors
  - Pulse animation for running agents
  - Completion checkmarks

### 2.3 Pipeline Components
- [ ] `components/pipeline/live-logs.tsx`
  - Scrolling log viewer
  - Auto-scroll toggle
  - Timestamp formatting
  - Log level indicators (info/success/warning/error)
  - Search/filter logs
- [ ] `components/pipeline/live-stats.tsx`
  - Dynamic counters (events, vendors, score)
  - Animated number transitions
  - Elapsed time display
- [ ] `components/pipeline/progress-bar.tsx`
  - Overall pipeline progress
  - Individual agent progress
  - Color-coded segments

### 2.4 Event Components
- [ ] `components/event/event-card.tsx`
  - Event thumbnail/image
  - Title and description
  - Location and dates
  - Score badge
  - Tier badge (color-coded)
  - Attendee count
  - Action buttons
- [ ] `components/event/event-table.tsx`
  - Sortable columns
  - Filterable rows
  - Pagination
  - Bulk actions
  - Export functionality
- [ ] `components/event/score-breakdown.tsx`
  - Bar charts for each score category
  - Overall score display
  - Visual indicators

### 2.5 Vendor Components
- [ ] `components/vendor/vendor-card.tsx`
  - Company logo/placeholder
  - Name and location
  - Contact info
  - Service category badges
  - Rating stars
  - Portfolio link
- [ ] `components/vendor/vendor-list.tsx`
  - Grid or list view toggle
  - Filter by category
  - Sort options
- [ ] `components/vendor/email-composer.tsx`
  - Rich text editor (or simple textarea)
  - Template selection
  - Variable insertion ({{event_name}}, etc.)
  - Preview mode

### 2.6 UI Primitives (shadcn wrappers)
- [ ] `components/ui/loading.tsx` - Loading states
- [ ] `components/ui/empty-state.tsx` - No data displays
- [ ] `components/ui/error-boundary.tsx` - Error handling
- [ ] `components/ui/page-header.tsx` - Consistent headers

**Deliverable:** Complete component library ready for page assembly

---

## Phase 3: Page Implementation (Days 8-14)

### 3.1 Home Page (`app/page.tsx`)
- [ ] Hero section with animated gradient
- [ ] Discovery form (industry, region, theme)
- [ ] Recent pipelines list
- [ ] Statistics overview
- [ ] Quick actions
- [ ] Responsive layout
- **Animations:** Fade-in on load, staggered children

### 3.2 Pipeline Page (`app/pipeline/[id]/page.tsx`)
- [ ] Header with pipeline ID and controls
- [ ] 6-agent grid visualization
- [ ] Real-time progress tracking
- [ ] Live logs panel
- [ ] Live stats panel
- [ ] Pause/Resume/Restart controls
- [ ] Results CTA (when complete)
- **Animations:** Agent card status transitions, progress bar updates, log scroll

### 3.3 Events List Page (`app/events/page.tsx`)
- [ ] Search and filter toolbar
- [ ] Tier tabs (All, Tier 1, Tier 2, Tier 3)
- [ ] Event cards grid
- [ ] Sort options
- [ ] Export button
- [ ] Pagination
- **Animations:** Card hover effects, filter transitions

### 3.4 Event Detail Page (`app/events/[id]/page.tsx`)
- [ ] Event header with key info
- [ ] Quick stats row
- [ ] Tabs: Overview, Scores, Vendors, Outreach
- [ ] Score breakdown visualization
- [ ] Intelligence panel
- [ ] Vendor list for this event
- [ ] Email outreach section
- **Animations:** Tab content transitions, score bar animations

### 3.5 Vendors Page (`app/vendors/page.tsx`)
- [ ] Search and filter
- [ ] Category tabs
- [ ] Vendor cards grid
- [ ] Bulk email selection
- [ ] Email composer modal
- **Animations:** Card reveals, modal transitions

### 3.6 Analytics Page (`app/analytics/page.tsx`)
- [ ] KPI cards (events, tier 1, vendors, etc.)
- [ ] Line chart (events over time)
- [ ] Pie chart (events by region/tier)
- [ ] Top events leaderboard
- [ ] Outreach performance stats
- **Animations:** Chart load animations, number counting

**Deliverable:** All 6 pages fully implemented with animations

---

## Phase 4: Integration & Testing (Days 15-18)

### 4.1 API Integration
- [ ] Connect to FastAPI backend
- [ ] Fetch pipeline status
- [ ] Fetch events list
- [ ] Fetch event details
- [ ] Fetch vendors
- [ ] Post new pipeline requests
- [ ] Error handling for API failures

### 4.2 Real-time Updates
- [ ] Implement Server-Sent Events (SSE) connection
- [ ] Listen for pipeline updates
- [ ] Update agent statuses in real-time
- [ ] Append new log entries
- [ ] Update statistics counters
- [ ] Handle connection drops/reconnects

### 4.3 Responsive Testing
- [ ] Test on desktop (1920px, 1440px, 1280px)
- [ ] Test on tablet (768px, 1024px)
- [ ] Test on mobile (375px, 414px)
- [ ] Fix layout issues
- [ ] Test touch interactions

### 4.4 Performance Optimization
- [ ] Lazy load heavy components
- [ ] Optimize images
- [ ] Minimize re-renders with React.memo
- [ ] Add loading states for slow operations
- [ ] Test with slow network throttling

### 4.5 Accessibility (a11y)
- [ ] Keyboard navigation works
- [ ] ARIA labels on interactive elements
- [ ] Color contrast ratios meet WCAG 2.1
- [ ] Screen reader compatibility
- [ ] Focus indicators visible

### 4.6 Cross-browser Testing
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

**Deliverable:** Production-ready frontend fully integrated with backend

---

## Dependencies & Risks

### Dependencies
- Backend API must be running for full testing
- WebSocket/SSE endpoint for real-time features
- Environment variables for API URLs

### Risk Mitigation
| Risk | Mitigation |
|------|------------|
| shadcn init conflicts | Backup first, use `git checkout` if needed |
| Animation performance | Test on low-end devices, reduce complexity if needed |
| API delays | Implement loading states and optimistic UI |
| Responsive issues | Use Tailwind breakpoints consistently |

---

## Success Criteria
- [ ] All 6 pages load without errors
- [ ] Dark/light mode toggle works instantly
- [ ] 6 agents display in parallel with smooth animations
- [ ] Real-time updates flow from backend to UI
- [ ] Mobile experience is fully functional
- [ ] Lighthouse score > 90 for performance
- [ ] No console errors or warnings

---

## Estimated Effort
- **Total:** 18 days (3.5 weeks)
- **Frontend Dev:** 14 days
- **Testing & Polish:** 4 days
