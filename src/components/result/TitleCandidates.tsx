import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy } from "lucide-react";

interface TitleCandidatesProps {
  data?: { id: number; title: string; char_count?: number; scores?: any }[];
}

const TitleCandidates = ({ data }: TitleCandidatesProps) => {
  const colors = ["bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-green-500", "bg-sky-500", "bg-blue-500", "bg-purple-500"];

  const defaultTitles = [
    { id: 1, title: "분석 결과를 기다리는 중...", color: "bg-gray-500" },
  ];

  const titles = data && data.length > 0
    ? data.map((item, idx) => ({
        id: item.id || idx + 1,
        title: item.title || "제목 없음",
        color: colors[idx % colors.length],
      }))
    : defaultTitles;

  return (
    <div className="space-y-4 p-4 bg-[#1a1a2e] rounded-xl">
      <h2 className="text-xl font-bold text-white mb-4">숏폼 제목 후보</h2>
      <div className="grid gap-3">
        {titles.map((t) => (
          <Card key={t.id} className="bg-[#2a2a40] border-none shadow-lg overflow-hidden border-l-4 border-l-transparent hover:border-l-indigo-500 transition-all">
            <CardContent className="p-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 flex-1 overflow-hidden">
                <Badge className={`${t.color} text-white font-bold w-6 h-6 flex items-center justify-center rounded-full p-0`}>
                  {t.id}
                </Badge>
                <span className="text-gray-100 font-medium truncate shrink-0">{t.title}</span>
                <span className="text-[10px] text-gray-500 font-mono shrink-0">({t.title.length}자)</span>
              </div>
              <Button size="icon" variant="ghost" className="h-8 w-8 text-gray-400 hover:text-white hover:bg-white/10 shrink-0">
                <Copy className="w-4 h-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default TitleCandidates;

