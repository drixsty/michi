/**
 * Dashboard Layout — wraps all dashboard views with the Sidebar/Navbar.
 */
import MainLayout from '@/components/layout/MainLayout';
import { OnboardingGuard } from '@/components/auth/OnboardingGuard';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <OnboardingGuard>
      <MainLayout>
        {children}
      </MainLayout>
    </OnboardingGuard>
  );
}
