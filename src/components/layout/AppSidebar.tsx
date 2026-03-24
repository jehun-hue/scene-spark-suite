import { useLocation, useNavigate } from "react-router-dom";
import {
  FolderOpen, Search, Flame, Clapperboard, Volume2,
  Image, Scissors, Upload, Wrench, Plus, ChevronDown
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const menuItems = [
  { icon: FolderOpen, label: "프로젝트", path: "/" },
  { icon: Search, label: "채널/영상 분석", path: "/result" },
  { icon: Flame, label: "대본작성", path: "/script" },
  { icon: Clapperboard, label: "후반작업", path: "/post" },
  { icon: Volume2, label: "사운드스튜디오", path: "/sound" },
  { icon: Image, label: "이미지/영상", path: "/media" },
  { icon: Scissors, label: "편집실", path: "/edit" },
  { icon: Upload, label: "업로드", path: "/upload" },
];

const AppSidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [toolsOpen, setToolsOpen] = useState(false);

  return (
    <aside className="w-[220px] min-w-[220px] h-full bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="p-3">
        <Button
          className="w-full gradient-primary gradient-primary-hover text-primary-foreground font-medium gap-2"
          onClick={() => navigate("/upload")}
        >
          <Plus className="w-4 h-4" />
          새 프로젝트
        </Button>
      </div>

      <nav className="flex-1 px-2 space-y-0.5">
        {menuItems.map((item) => {
          const active = location.pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors relative ${
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50"
              }`}
            >
              {active && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-primary" />
              )}
              <item.icon className="w-4 h-4 shrink-0" />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="p-2 border-t border-sidebar-border">
        <button
          onClick={() => setToolsOpen(!toolsOpen)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground hover:bg-sidebar-accent/50 transition-colors"
        >
          <Wrench className="w-4 h-4" />
          도구모음
          <ChevronDown className={`w-3.5 h-3.5 ml-auto transition-transform ${toolsOpen ? "rotate-180" : ""}`} />
        </button>
        {toolsOpen && (
          <div className="px-3 py-2 text-xs text-muted-foreground">
            추가 도구가 여기에 표시됩니다.
          </div>
        )}
      </div>
    </aside>
  );
};

export default AppSidebar;
