# Component Library

GET INN's frontend uses a comprehensive component library built on shadcn/ui, which provides accessible, customizable, and reusable UI components.

## Overview

The component library serves as the foundation for all UI elements in the application, ensuring:

1. Consistent visual design and user experience
2. Accessibility compliance
3. Responsive behavior across devices
4. Customizable theming
5. Reusable patterns for rapid development

## shadcn/ui Integration

The application uses [shadcn/ui](https://ui.shadcn.com/), which is built on:

- [Radix UI](https://www.radix-ui.com/) for accessible primitives
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [class-variance-authority](https://cva.style/docs) for component variants

### Installation and Configuration

Components are added using the shadcn/ui CLI:

```bash
npx shadcn-ui@latest add button
```

Configuration is maintained in `components.json`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

## Core Components

### Layout Components

| Component | Description | Usage |
|-----------|-------------|-------|
| `Card` | Container for grouped content | Content sections, dashboards |
| `Sheet` | Slide-in panel | Navigation, filters, details |
| `Tabs` | Tabbed interface | Content organization |
| `ScrollArea` | Scrollable container | Long content, lists |

### Input Components

| Component | Description | Usage |
|-----------|-------------|-------|
| `Button` | Interactive button | Actions, submissions |
| `Input` | Text input field | Forms, search |
| `Select` | Dropdown selection | Options selection |
| `Checkbox` | Binary selection | Multiple selections |
| `RadioGroup` | Exclusive selection | Single selection from options |
| `Switch` | Toggle control | Binary settings |
| `Slider` | Range selection | Numeric range input |

### Data Display Components

| Component | Description | Usage |
|-----------|-------------|-------|
| `Table` | Tabular data | Data lists, comparison |
| `Avatar` | User representation | User profiles, comments |
| `Badge` | Status indicator | Notifications, labels |
| `Progress` | Progress indicator | Loading, completion |

### Feedback Components

| Component | Description | Usage |
|-----------|-------------|-------|
| `Alert` | Information display | Notifications, warnings |
| `Toast` | Temporary notification | Action confirmation |
| `Dialog` | Modal interaction | Confirmations, forms |
| `Tooltip` | Contextual information | Help text, explanations |

## Component Customization

### Theme Integration

Components use CSS variables from the theme system:

```css
/* In src/index.css */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  --popover: 0 0% 100%;
  --popover-foreground: 222.2 84% 4.9%;
  --primary: 258 75% 55%; /* GET INN purple */
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96.1%;
  --accent-foreground: 222.2 47.4% 11.2%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 258 75% 55%;
  --radius: 0.5rem;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;
  /* ...and so on */
}
```

### Component Variants

Components use class-variance-authority (CVA) for variants:

```tsx
// src/components/ui/button.tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);
```

## Custom Components

Beyond the shadcn/ui components, the application includes custom components specific to GET INN's needs:

### Application-Specific Components

| Component | Description | Usage |
|-----------|-------------|-------|
| `StatusBadge` | Restaurant health status | Dashboard, overview pages |
| `MetricCard` | KPI display | Dashboard metrics |
| `ReconciliationProgress` | Multi-step progress | Supplier reconciliation |
| `MenuItemChart` | Item performance chart | Menu analysis |
| `TrainingProgress` | Progress tracker | Labor onboarding |

### Example Custom Component

```tsx
// src/components/custom/StatusBadge.tsx
import { cn } from "@/lib/utils";

type StatusType = "green" | "orange" | "red";

interface StatusBadgeProps {
  status: StatusType;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

const statusLabels: Record<StatusType, string> = {
  green: "Healthy",
  orange: "Warning",
  red: "Critical",
};

const statusColors: Record<StatusType, string> = {
  green: "bg-green-500",
  orange: "bg-orange-500",
  red: "bg-red-500",
};

export function StatusBadge({
  status,
  size = "md",
  showLabel = true,
  className,
}: StatusBadgeProps) {
  const sizeClasses = {
    sm: "h-2 w-2",
    md: "h-3 w-3",
    lg: "h-4 w-4",
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn(
          "rounded-full",
          statusColors[status],
          sizeClasses[size]
        )}
      />
      {showLabel && (
        <span className="text-sm font-medium">{statusLabels[status]}</span>
      )}
    </div>
  );
}
```

## Form Integration

The application integrates React Hook Form with the component library for form handling:

```tsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const formSchema = z.object({
  name: z.string().min(2, {
    message: "Name must be at least 2 characters.",
  }),
  email: z.string().email({
    message: "Please enter a valid email address.",
  }),
});

export function ProfileForm() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      email: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Handle form submission
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="Your name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input placeholder="email@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Save</Button>
      </form>
    </Form>
  );
}
```

## Accessibility Features

The component library prioritizes accessibility through:

1. **ARIA Attributes**: Proper labeling and roles
2. **Keyboard Navigation**: Full keyboard support
3. **Focus Management**: Clear focus indicators
4. **Screen Reader Support**: Appropriate text alternatives
5. **Color Contrast**: WCAG 2.1 compliant contrast ratios

### Example: Accessible Dialog

```tsx
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export function AccessibleDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Accessible Dialog Title</DialogTitle>
          <DialogDescription>
            This dialog is fully keyboard navigable, has proper ARIA attributes,
            and manages focus correctly.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Dialog content goes here...</p>
        </div>
        <DialogTrigger asChild>
          <Button className="mt-4">Close</Button>
        </DialogTrigger>
      </DialogContent>
    </Dialog>
  );
}
```

## Component Usage Guidelines

### When to Use Components

- **Prefer existing components** over creating new ones when possible
- **Extend existing components** with variants instead of creating similar components
- **Create new components** only when existing ones cannot be adapted

### Component Composition

Components are designed for composition:

```tsx
// Example of component composition
<Card>
  <CardHeader>
    <CardTitle>Sales Overview</CardTitle>
    <CardDescription>Summary of monthly sales performance</CardDescription>
  </CardHeader>
  <CardContent>
    <div className="h-[240px]">
      <BarChart data={salesData} />
    </div>
  </CardContent>
  <CardFooter className="flex justify-between">
    <Button variant="ghost">Previous Month</Button>
    <Button>Export Data</Button>
  </CardFooter>
</Card>
```

## Further Resources

- [shadcn/ui Documentation](https://ui.shadcn.com/docs)
- [Radix UI Primitives](https://www.radix-ui.com/primitives)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Hook Form Documentation](https://react-hook-form.com/)