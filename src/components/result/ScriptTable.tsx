import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Terminal, Timer, Tv2, Image as ImageIcon } from "lucide-react";

interface ScriptTableProps {
  data?: any[];
  thumbnails?: { timecode: string; thumbnail_base64: string | null }[];
}

const dummyScriptItems = [
  { id: 1, mode: "S", audio: "안녕하세요, 오늘은 미래 기술에 대해 알아보겠습니다.", subtitle: "미래 기술 개요", time: "15s", video: "사회자가 정면을 보고 인사를 함", tcode: "00:00:00.000", color: "bg-blue-500" },
  { id: 2, mode: "N", audio: "(배경음악) 웅장한 오케스트라 사운드", subtitle: "(BGM: Epic)", time: "05s", video: "도시의 화려한 야경 드론샷", tcode: "00:00:15.000", color: "bg-green-500" },
  { id: 3, mode: "A", audio: "지금 바로 구독하고 더 많은 정보를 받아보세요!", subtitle: "구독 버튼 강조", time: "08s", video: "화면 하단에 구독, 좋아요 애니메이션", tcode: "00:00:20.000", color: "bg-orange-500" },
  { id: 4, mode: "S", audio: "인공지능이 우리 삶을 어떻게 바꿀까요?", subtitle: "AI 라이프스타일", time: "12s", video: "사람과 인공지능이 협동하는 몽타주", tcode: "00:00:28.000", color: "bg-blue-500" },
  { id: 5, mode: "N", audio: "(침묵) 신비로운 분위기의 효과음", subtitle: "긴장감 조성", time: "07s", video: "연구실 문이 천천히 열리는 샷", tcode: "00:00:40.000", color: "bg-green-500" },
];

const ScriptTable = ({ data, thumbnails }: ScriptTableProps) => {
  const items = data ? data.map((item, idx) => ({
    id: idx + 1,
    mode: item.mode || "S",
    audio: item.source_segment || item.audio || "",
    subtitle: item.subtitle_text || item.subtitle || "자막 없음",
    time: item.time || "3s",
    video: item.edit_event || item.video || "화면 연출 지시",
    tcode: item.timecode || item.tcode || "00:00:00.000",
    color: item.mode === "N" ? "bg-green-500" : item.mode === "A" ? "bg-orange-500" : "bg-blue-500"
  })) : dummyScriptItems;

  const findThumbnail = (tcode: string) => {
    return thumbnails?.find(t => t.timecode === tcode)?.thumbnail_base64;
  };

  return (
    <Card className="bg-[#1a1a2e] border-none shadow-2xl overflow-hidden rounded-2xl ring-1 ring-white/5">
      <CardHeader className="py-4 px-6 border-b border-white/5">
        <CardTitle className="text-xl font-bold text-white flex items-center justify-between">
          장면별 대본 구성
          <Terminal className="w-5 h-5 text-indigo-400 opacity-50" />
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader className="bg-white/5">
              <TableRow className="border-b border-white/5 hover:bg-transparent">
                <TableHead className="w-[50px] text-gray-500 font-black">#</TableHead>
                <TableHead className="w-[80px] text-gray-400 text-center uppercase tracking-tighter">모드</TableHead>
                <TableHead className="text-gray-400 font-bold max-w-[300px]">오디오 내용</TableHead>
                <TableHead className="text-gray-400 font-bold min-w-[120px]">효과자막</TableHead>
                <TableHead className="text-gray-400 font-bold">예상시간</TableHead>
                <TableHead className="text-gray-400 font-bold max-w-[200px]">영상화면 지시</TableHead>
                <TableHead className="text-gray-400 font-bold">타임코드</TableHead>
                <TableHead className="text-gray-400 font-bold text-right pt-2"><ImageIcon className="w-4 h-4 ml-auto opacity-50" /></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => {
                const thumb = findThumbnail(item.tcode);
                return (
                  <TableRow key={item.id} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
                    <TableCell className="text-gray-500 font-black text-[12px]">{item.id}</TableCell>
                    <TableCell className="text-center">
                      <Badge className={`${item.color} text-white font-black w-7 h-7 flex items-center justify-center rounded-lg shadow-inner`}>
                        {item.mode}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-gray-100 font-medium text-sm drop-shadow-sm py-5 leading-relaxed">
                      {item.audio}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={`border-white/20 text-indigo-300 font-bold text-[11px] px-2.5 py-1 bg-indigo-900/40 tracking-tightest`}>
                        {item.subtitle}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-orange-400 font-black text-xs">
                      <div className="flex items-center gap-1.5 animate-pulse">
                        <Timer className="w-3.5 h-3.5" />
                        {item.time}
                      </div>
                    </TableCell>
                    <TableCell className="text-gray-400 text-[12px] leading-snug tracking-tighter italic">
                      <div className="flex items-start gap-2">
                         <Tv2 className="w-3.5 h-3.5 mt-0.5 opacity-30 group-hover:opacity-100 transition-opacity" />
                         {item.video}
                      </div>
                    </TableCell>
                    <TableCell className="text-gray-500 font-mono text-[11px]">
                      {item.tcode}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="w-[160px] h-[90px] ml-auto bg-white/5 rounded-lg border border-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors overflow-hidden">
                        {thumb ? (
                          <img src={thumb} alt="Thumbnail" className="w-full h-full object-cover rounded-lg" />
                        ) : (
                          <ImageIcon className="w-6 h-6 text-gray-700 opacity-30" />
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default ScriptTable;
