# ONYX UI Component Library

A comprehensive, accessible, and beautifully animated UI component library built for the ONYX Security Intelligence Platform.

## 📦 Installation

All components are already included in the ONYX frontend. Import from the UI components library:

```jsx
import { Button, Card, Modal, DataTable } from "../components/ui";
```

---

## 🧱 Core Components

### Button

Enhanced button with variants, sizes, and animations.

```jsx
import { Button, IconButton, ButtonGroup } from '../components/ui';

// Basic usage
<Button variant="primary">Click me</Button>

// With icon
<Button icon={PlusIcon} iconPosition="left">Add Item</Button>

// Loading state
<Button loading>Processing...</Button>

// Variants: primary, secondary, success, danger, warning, purple, ghost, outline, glass, gradient
// Sizes: xs, sm, md, lg, xl
```

### Card

Versatile card components with glass morphism.

```jsx
import { Card, CardHeader, CardContent, CardFooter, ListCard, StatsCard, GradientCard } from '../components/ui';

<Card variant="glass" hover onClick={handleClick}>
  <CardHeader title="Title" subtitle="Subtitle" icon={ShieldIcon} />
  <CardContent>Content here</CardContent>
  <CardFooter>Footer actions</CardFooter>
</Card>

// ListCard - Clickable list item
<ListCard
  title="Project Name"
  subtitle="Last scanned 2 hours ago"
  icon={FolderIcon}
  badge={<Badge>Active</Badge>}
  onClick={handleClick}
/>
```

### Modal

Accessible modal dialogs with animations.

```jsx
import { Modal, ConfirmModal } from '../components/ui';

<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Modal Title"
  size="md" // sm, md, lg, xl, full
>
  <p>Modal content</p>
</Modal>

// Confirmation dialog
<ConfirmModal
  isOpen={isOpen}
  onClose={handleClose}
  onConfirm={handleConfirm}
  title="Delete Item"
  message="Are you sure?"
  confirmText="Delete"
  variant="danger"
/>
```

### DataTable

Advanced data table with sorting, filtering, pagination.

```jsx
import { DataTable } from "../components/ui";

const columns = [
  { key: "name", label: "Name", sortable: true },
  { key: "status", label: "Status", render: (val) => <Badge>{val}</Badge> },
];

<DataTable
  columns={columns}
  data={data}
  sortable
  filterable
  paginated
  pageSize={10}
  selectable
  onRowClick={handleRowClick}
  rowActions={[
    { label: "Edit", icon: PencilIcon, onClick: handleEdit },
    { label: "Delete", icon: TrashIcon, onClick: handleDelete, danger: true },
  ]}
/>;
```

---

## 📊 Display Components

### Badge

Status and severity badges.

```jsx
import { Badge, SeverityBadge, StatusBadge } from '../components/ui';

<Badge variant="success">Active</Badge>
<SeverityBadge severity="critical" />
<StatusBadge status="completed" />
```

### Avatar

User avatars with fallback initials.

```jsx
import { Avatar, AvatarGroup } from '../components/ui';

<Avatar src={user.avatar} name={user.name} size="md" />

<AvatarGroup max={3}>
  <Avatar name="John Doe" />
  <Avatar name="Jane Smith" />
  <Avatar name="Bob Wilson" />
</AvatarGroup>
```

### Progress

Progress indicators.

```jsx
import { Progress, CircularProgress, SegmentedProgress } from '../components/ui';

<Progress value={75} showValue />
<CircularProgress value={75} size={100} />
<SegmentedProgress segments={[
  { value: 30, color: 'red', label: 'Critical' },
  { value: 50, color: 'yellow', label: 'Warning' },
  { value: 20, color: 'green', label: 'Clean' },
]} />
```

### StatCard

Statistics display cards.

```jsx
import { StatCard, StatsGrid, CompactStat } from "../components/ui";

<StatsGrid columns={4}>
  <StatCard
    title="Total Scans"
    value={1234}
    trend="up"
    trendValue="+12%"
    icon={ChartIcon}
    variant="primary"
  />
</StatsGrid>;
```

---

## 📈 Chart Components

Lightweight chart components without external dependencies.

```jsx
import { BarChart, DonutChart, LineChart, GaugeChart, Sparkline } from '../components/ui';

// Bar Chart
<BarChart
  data={[
    { label: 'Jan', value: 100, color: 'from-blue-500 to-cyan-500' },
    { label: 'Feb', value: 200 },
  ]}
  height={200}
  showValues
/>

// Donut Chart
<DonutChart
  data={[
    { label: 'Critical', value: 10, color: '#ef4444' },
    { label: 'High', value: 25, color: '#f97316' },
  ]}
  size={200}
  centerValue={35}
  centerLabel="Issues"
/>

// Line Chart with area
<LineChart
  data={[{ value: 10 }, { value: 20 }, { value: 15 }]}
  height={100}
  showArea
  showDots
/>

// Sparkline (inline)
<Sparkline data={[10, 20, 15, 25, 30]} width={100} height={30} />
```

---

## 🎨 Animation Components

```jsx
import {
  PageTransition,
  FadeIn,
  ScaleIn,
  SlideIn,
  StaggeredList,
  HoverScale,
} from '../components/ui';

// Page transitions
<PageTransition>
  <YourPageContent />
</PageTransition>

// Fade in with direction
<FadeIn delay={0.2} direction="up">
  <Card>Content</Card>
</FadeIn>

// Staggered list animation
<StaggeredList staggerDelay={0.05}>
  {items.map(item => <ListItem key={item.id} />)}
</StaggeredList>
```

---

## 📝 Form Components

### Input

Enhanced input with validation states.

```jsx
import { Input, TextArea, Select } from '../components/ui';

<Input
  label="Email"
  type="email"
  icon={EnvelopeIcon}
  error="Invalid email"
  required
/>

<Input
  type="password"
  showPasswordToggle
/>

<TextArea
  label="Description"
  rows={4}
  hint="Enter a detailed description"
/>

<Select
  label="Priority"
  options={[
    { value: 'low', label: 'Low' },
    { value: 'high', label: 'High' },
  ]}
/>
```

### Switch

Toggle switches with groups.

```jsx
import { Switch, SwitchGroup } from '../components/ui';

<Switch
  checked={enabled}
  onChange={setEnabled}
  label="Enable notifications"
/>

<SwitchGroup
  items={[
    { id: 'email', label: 'Email', checked: true },
    { id: 'sms', label: 'SMS', checked: false },
  ]}
  onChange={handleChange}
/>
```

---

## 🔔 Feedback Components

### Notification

Toast notifications.

```jsx
import { Notification, NotificationContainer } from "../components/ui";

// In your app root
<NotificationContainer />;

// Usage
Notification.success("Operation completed!");
Notification.error("Something went wrong");
Notification.warning("Please review");
Notification.info("New update available");
```

### Modal & Tooltip

```jsx
import { Tooltip } from "../components/ui";

<Tooltip content="Helpful information" position="top">
  <Button>Hover me</Button>
</Tooltip>;
```

---

## 🎣 Custom Hooks

```jsx
import {
  useDebounce,
  useLocalStorage,
  useMediaQuery,
  useIsMobile,
  useOnClickOutside,
  useKeyPress,
  useCopyToClipboard,
  useToggle,
  useAnimatedCounter,
} from "../components/ui";

// Debounce search input
const debouncedSearch = useDebounce(searchQuery, 300);

// Persist state
const [theme, setTheme] = useLocalStorage("theme", "dark");

// Responsive
const isMobile = useIsMobile();

// Click outside detection
const ref = useRef();
useOnClickOutside(ref, () => setOpen(false));

// Keyboard shortcuts
useKeyPress("k", () => openSearch(), { ctrl: true });

// Copy to clipboard
const { copy, copiedText } = useCopyToClipboard();

// Toggle state
const { value: isOpen, toggle, setTrue, setFalse } = useToggle(false);
```

---

## 🎯 Layout Components

```jsx
import {
  Container,
  Grid,
  Flex,
  Stack,
  Section,
  PageHeader,
  Breadcrumb,
} from "../components/ui";

// Responsive container
<Container size="lg" padding>
  <PageHeader
    title="Dashboard"
    description="Overview of your security posture"
    icon={ShieldIcon}
    breadcrumb={[{ label: "Home", href: "/" }, { label: "Dashboard" }]}
    actions={<Button>New Scan</Button>}
  />

  <Grid cols={4} gap={6}>
    <StatCard />
    <StatCard />
    <StatCard />
    <StatCard />
  </Grid>

  <Section title="Recent Activity" action={<Button size="sm">View All</Button>}>
    <Stack gap={4}>
      <ListCard />
      <ListCard />
    </Stack>
  </Section>
</Container>;
```

---

## 🎨 Design Tokens

The component library uses CSS variables for consistent theming:

```css
:root {
  --bg-primary: #0a0e1a;
  --bg-secondary: #111827;
  --text-primary: #f9fafb;
  --gradient-primary: linear-gradient(135deg, #3b82f6, #8b5cf6);
  --gradient-success: linear-gradient(135deg, #10b981, #059669);
}
```

---

## 📱 Responsive Design

All components are responsive by default. Use the responsive hooks:

```jsx
const isMobile = useIsMobile(); // < 768px
const isTablet = useIsTablet(); // 768px - 1024px
const isDesktop = useIsDesktop(); // > 1024px

// Or media queries
const isLargeScreen = useMediaQuery("(min-width: 1280px)");
```

---

## ♿ Accessibility

All components follow WCAG guidelines:

- Keyboard navigation
- ARIA labels and roles
- Focus management
- Screen reader support
- Color contrast compliance

---

## 🚀 Performance

- Tree-shakeable exports
- Lazy-loaded animations with Framer Motion
- Optimized re-renders with React.memo
- CSS-based animations where possible
