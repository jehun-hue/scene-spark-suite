import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy } from "lucide-react";

interface TitleItem {
  id: number;
  title: string;
  color: string;
}

const titles: TitleItem[] = [
  { id: 1, title: "세계를 뒤흔들 혁신적인 기술의 탄생", color: "bg-red-500" },
  { id: 2, title: "당신이 몰랐던 일상의 숨겨진 미스터리", color: "bg-orange-500" },
  { id: 3, title: "단 1분 만에 배우는 고효율 시간관리법", color: "bg-yellow-500" },
  { id: 4, title: "미래를 바꾸는 작은 습관의 놀라운 힘", color: "bg-green-500" },
  { id: 5, title: "지금 당장 시작해야 할 재테크 필수 전략", color: "bg-sky-500" },
  { id: 6, title: "성공하는 사람들의 공통적인 아침 루틴", color: "bg-blue-500" },
  { id: 7, title: "인생의 터닝포인트를 만드는 7가지 방법", color: "bg-purple-500" },
];

const TitleCandidates = () => {
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
