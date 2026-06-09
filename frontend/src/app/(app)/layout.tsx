export default function AppLayout({ children }: { children: React.ReactNode }) {
  // The full Navbar arrives in Phase 7; for now this just frames protected pages.
  return <div className="min-h-screen">{children}</div>;
}
