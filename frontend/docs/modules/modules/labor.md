# AI Labor Module

The AI Labor module streamlines staff onboarding and training processes, providing restaurant managers with tools to track employee progress and ensure consistent training across locations.

## Overview

The AI Labor module focuses primarily on staff onboarding, with features designed to:

1. Track training progress for new employees
2. Manage training schedules across multiple locations
3. Provide insights into staffing efficiency
4. Ensure consistent onboarding experience

## Key Components

### Onboarding Dashboard

The main interface for the AI Labor module includes:

- **Overview Dashboard**: High-level view of onboarding across all locations
- **Staff List**: Filterable list of employees in the onboarding process
- **Training Schedule**: Calendar view of planned training activities
- **Progress Tracking**: Visual indicators of onboarding completion percentage

### Individual Staff View

Detailed view for each employee includes:

- **Personal Information**: Employee details and position
- **Training Steps**: Checklist of required training items
- **Progress Timeline**: Visual timeline of completed steps
- **Upcoming Steps**: Next actions required in the onboarding process
- **Notes & Feedback**: Training feedback and special notes

## Implementation Details

### Staff Onboarding Process

The onboarding process follows these steps:

1. Manager creates new staff onboarding profile
2. System generates personalized onboarding checklist based on position
3. Manager and staff member update progress as training steps are completed
4. System tracks completion dates and overall progress
5. Analytics provide insights into onboarding efficiency

### Data Structure

```typescript
interface StaffOnboarding {
  id: string;
  name: string;
  email: string;
  position: string;
  location: string;
  start_date: string;
  exam_date: string;
  progress_percentage: number;
  status: 'in_progress' | 'completed' | 'terminated';
  steps: {
    id: string;
    name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    completion_date?: string;
    notes?: string;
  }[];
}
```

### Main Components

The module is built using these key components:

1. **OnboardingDashboard**: Main container component for the module
2. **OnboardingStats**: Summary statistics and charts
3. **StaffList**: Interactive staff list with filtering and sorting
4. **ProgressBar**: Visual indicator of completion status
5. **StaffDetail**: Individual staff view with training details

### API Integration

The module connects to these backend endpoints:

```typescript
// Fetch all staff onboarding records
const fetchOnboardingRecords = async () => {
  const { data } = await api.get('/v1/api/labor/onboarding');
  return data;
};

// Fetch details for a specific staff member
const fetchStaffDetail = async (staffId: string) => {
  const { data } = await api.get(`/v1/api/labor/onboarding/${staffId}`);
  return data;
};

// Update onboarding step status
const updateStepStatus = async (staffId: string, stepId: string, status: string, notes?: string) => {
  const { data } = await api.put(`/v1/api/labor/onboarding/${staffId}/steps/${stepId}`, {
    status,
    notes
  });
  return data;
};
```

## User Interactions

### Creating New Staff Profile

1. User clicks "Add Staff" button on Onboarding Dashboard
2. Form appears to enter staff details (name, position, start date)
3. User selects training template based on position
4. System creates staff record and generates onboarding plan
5. User is redirected to the new staff profile

### Updating Training Progress

1. User navigates to staff detail page
2. User checks completed training items
3. System updates progress percentage
4. If all required items are complete, system marks onboarding as completed

### Filtering and Searching

1. User can filter staff list by:
   - Location
   - Position
   - Status (in progress, completed, terminated)
   - Date range (start date)
2. User can search by staff name

## Future Enhancements

Planned improvements to the AI Labor module include:

1. **Performance Tracking**: Add post-onboarding performance metrics
2. **Training Materials**: Integrated training content and assessments
3. **Certification Management**: Track and manage staff certifications
4. **Schedule Integration**: Connect with scheduling system for training slots
5. **Mobile Support**: Enhanced mobile experience for on-the-floor training tracking

## Integration with Other Modules

The AI Labor module integrates with:

- **Dashboard**: Key labor metrics are displayed on the main dashboard
- **Settings**: Configuration options for training templates and requirements

## Technical Implementation Notes

- Uses React Query for data fetching and caching
- Implements React Hook Form for form state management
- Utilizes shadcn/ui components for consistent UI design
- Uses a context provider for module-wide state