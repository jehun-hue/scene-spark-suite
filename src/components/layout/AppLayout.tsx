import AppHeader from "./AppHeader";
import AppSidebar from "./AppSidebar";

const AppLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <AppHeader />
      <div className="flex flex-1 overflow-hidden">
        <AppSidebar />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
