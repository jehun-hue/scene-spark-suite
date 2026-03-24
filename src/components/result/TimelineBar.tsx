import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const timelineData = [
  { label: "AI 나레이션", color: "bg-[#3b82f6]", width: "35%" },
  { label: "원본 대사", color: "bg-[#f97316]", width: "20%" },
  { label: "배경 나레이션", color: "bg-[#22c55e]", width: "25%" },
  { label: "현장 액션", color: "bg-[#ec4899]", width: "20%" },
];

const TimelineBar = () => {
  return (
    <Card className="bg-[#1a1a2e] border-none shadow-xl overflow-hidden rounded-xl h-44 flex flex-col justify-center">
      <CardHeader className="py-2 px-6">
        <CardTitle className="text-xl font-bold text-white flex items-center justify-between">
          타임라인 분석
          <span className="text-xs text-indigo-400 font-mono tracking-tight uppercase">Time Code: 00:03:45.000</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="px-6 space-y-6">
        {/* Horizontal Timeline Bar */}
        <div className="relative h-12 w-full rounded-2xl overflow-hidden bg-white/5 drop-shadow-xl flex">
          {timelineData.map((t, idx) => (
            <div
              key={idx}
              className={`h-full ${t.color} first:rounded-l-2xl last:rounded-r-2xl border-x border-white/10 hover:opacity-90 transition-opacity cursor-help`}
              style={{ width: t.width }}
              title={t.label}
            ></div>
          ))}
          <div className="absolute top-0 left-1/3 w-[2px] h-full bg-red-500 shadow-[0_0_10px_red] animate-pulse"></div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-6 pt-2">
          {timelineData.map((t, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <div className={`w-3.5 h-3.5 ${t.color} rounded-full ring-2 ring-white/10`}></div>
              <span className="text-[13px] font-bold text-gray-300 uppercase tracking-tighter">{t.label}</span>
              <Badge variant="outline" className="text-[10px] py-0 px-1 border-white/10 text-gray-500 font-mono">
                {t.width}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default TimelineBar;
