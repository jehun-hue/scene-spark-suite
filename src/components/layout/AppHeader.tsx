import { Check, Settings, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const AppHeader = () => {
  const navigate = useNavigate();

  return (
    <header className="h-14 flex items-center justify-between px-4 border-b border-border bg-card">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center text-primary-foreground font-bold text-sm">
          A
        </div>
        <span className="font-semibold text-foreground">All In One Production</span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-muted-foreground">v1.0</span>
      </div>

      <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground text-center flex-1 justify-center">
        실시간 제작 비용:
        <span className="font-semibold text-foreground ml-1">₩ 0.00</span>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground ml-6">
          <Check className="w-3.5 h-3.5 text-green-500" />
          자동 저장됨
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button 
          variant="outline" 
          size="sm" 
          className="gap-1.5 hover:bg-indigo-500/10 hover:text-indigo-400 border-white/5"
          onClick={() => navigate("/settings")}
        >
          <Settings className="w-3.5 h-3.5" />
          API 설정
        </Button>
        <Button variant="outline" size="sm" className="gap-1.5 border-white/5">
          <MessageSquare className="w-3.5 h-3.5" />
          피드백
        </Button>
      </div>
    </header>
  );
};

export default AppHeader;
