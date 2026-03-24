import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Gauge, Layers, SortAsc, RefreshCw } from "lucide-react";

const cards = [
  { title: "텍스트 일치율", value: "11.5%", icon: Gauge, color: "text-blue-400" },
  { title: "구조 유사도", value: "12.5%", icon: Layers, color: "text-orange-400" },
  { title: "순서 유사도", value: "9.5%", icon: SortAsc, color: "text-green-400" },
  { title: "회피 전환율", value: "96.5%", icon: RefreshCw, color: "text-purple-400", highlight: true },
];

const ContentIdCards = () => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 p-4 bg-[#1a1a2e] rounded-xl">
      {cards.map((c, idx) => (
        <Card
          key={idx}
          className={`group bg-[#2a2a40] border-none shadow-2xl overflow-hidden rounded-2xl ring-1 ring-white/5 hover:ring-indigo-500/50 transition-all duration-500 hover:-translate-y-2 cursor-pointer ${
            c.highlight ? "bg-gradient-to-br from-[#2a2a40] to-purple-900/40" : ""
          }`}
        >
          <CardHeader className="p-5 flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-black text-gray-500 uppercase tracking-widest">{c.title}</CardTitle>
            <div className={`p-2.5 rounded-xl bg-white/5 group-hover:bg-white/10 group-hover:scale-110 transition-all duration-300`}>
              <c.icon className={`w-5 h-5 ${c.color} drop-shadow-[0_0_8px_rgba(0,0,0,0.5)]`} />
            </div>
          </CardHeader>
          <CardContent className="p-5 pt-0 space-y-4">
            <div className="flex flex-col gap-1">
              <span className={`text-4xl font-black ${c.highlight ? "text-purple-400 drop-shadow-[0_4px_10px_rgba(168,85,247,0.5)]" : "text-gray-100"}`}>
                {c.value}
              </span>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${c.color.replace('text', 'bg')} opacity-60 rounded-full transition-all duration-1000 group-hover:opacity-100`}
                  style={{ width: c.value }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default ContentIdCards;
