import { Archive, FileText, Layout, Scissors, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAnalysisStore } from "@/stores/analysisStore";
import { exportFCPXML, exportPremiere, exportSRT, exportZip } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

const ExportButtons = () => {
  const { result } = useAnalysisStore();
  const { toast } = useToast();

  const handleExport = async (type: 'fcp' | 'premiere' | 'srt') => {
    if (!result) {
      toast({ title: "내보내기 실패", description: "분석 결과가 존재하지 않습니다.", variant: "destructive" });
      return;
    }

    try {
      if (type === 'fcp') await exportFCPXML(result);
      else if (type === 'premiere') await exportPremiere(result);
      else if (type === 'srt') await exportSRT(result);
      
      toast({ title: "내보내기 성공", description: "파일 다운로드가 시작되었습니다." });
    } catch (error: any) {
      toast({ title: "내보내기 에러", description: error.message, variant: "destructive" });
    }
  };

  return (
    <div className="space-y-6 pt-4 bg-[#1a1a2e] rounded-xl">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Button 
          onClick={() => handleExport('fcp')}
          className="bg-[#22c55e] hover:bg-[#16a34a] text-white font-bold h-12 gap-3 shadow-lg transition-transform hover:-translate-y-1"
        >
          <Archive className="w-5 h-5" />
          Final Cut Pro
        </Button>
        <Button 
          onClick={() => handleExport('premiere')}
          className="bg-[#3b82f6] hover:bg-[#2563eb] text-white font-bold h-12 gap-3 shadow-lg transition-transform hover:-translate-y-1"
        >
          <Archive className="w-5 h-5" />
          Premiere Pro
        </Button>
        <Button 
          onClick={() => handleExport('srt')}
          className="bg-[#6b7280] hover:bg-[#4b5563] text-white font-bold h-12 gap-3 shadow-lg transition-transform hover:-translate-y-1"
        >
          <Download className="w-5 h-5" />
          SRT 자막
        </Button>
      </div>

      <Card className="bg-[#24243a] border-none shadow-md overflow-hidden ring-1 ring-white/5 p-2">
        <Tabs defaultValue="script" className="w-full">
          <TabsList className="bg-transparent grid grid-cols-3 gap-2">
            <TabsTrigger value="script" className="data-[state=active]:bg-[#3b82f6] data-[state=active]:text-white data-[state=inactive]:text-gray-400 gap-2 font-bold py-2.5">
              <FileText className="w-4 h-4" />
              대본 복사
            </TabsTrigger>
            <TabsTrigger value="preview" className="data-[state=active]:bg-[#3b82f6] data-[state=active]:text-white data-[state=inactive]:text-gray-400 gap-2 font-bold py-2.5">
              <Layout className="w-4 h-4" />
              미리보기
            </TabsTrigger>
            <TabsTrigger value="edit" className="data-[state=active]:bg-[#3b82f6] data-[state=active]:text-white data-[state=inactive]:text-gray-400 gap-2 font-bold py-2.5">
              <Scissors className="w-4 h-4" />
              편집점
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </Card>
    </div>
  );
};

export default ExportButtons;
