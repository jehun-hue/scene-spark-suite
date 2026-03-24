import { Check, Settings, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

const AppHeader = () => {
  return (
    <header className="h-14 flex items-center justify-between px-4 border-b border-border bg-card">
      {/* Left: Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center text-primary-foreground font-bold text-sm">
          A
        </div>
        <span className="font-semibold text-foreground">All In One Production</span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-muted-foreground">v1.0</span>
      </div>

      {/* Center: Cost */}
      <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground">
        실시간 제작 비용:
        <span className="font-semibold text-foreground">₩ 0.00</span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mr-2">
          <Check className="w-3.5 h-3.5 text-badge-green" />
          자동 저장됨
        </div>
        <Button variant="outline" size="sm" className="gap-1.5">
          <Settings className="w-3.5 h-3.5" />
          API 설정
        </Button>
        <Button variant="outline" size="sm" className="gap-1.5">
          <MessageSquare className="w-3.5 h-3.5" />
          피드백
        </Button>
      </div>
    </header>
  );
};

export default AppHeader;
