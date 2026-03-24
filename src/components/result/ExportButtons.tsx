import { Archive, FileText, Layout, Scissors, Download, Film, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAnalysisStore } from "@/stores/analysisStore";
import { exportFCPXML, exportPremiere, exportSRT, exportZip, renderShort } from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import { useState, useRef } from "react";

const ExportButtons = () => {
  const { result } = useAnalysisStore();
  const { toast } = useToast();
  const [isRendering, setIsRendering] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleRenderRequest = () => {
    if (!result) {
      toast({ title: "데이터 없음", description: "분석 결과가 없습니다.", variant: "destructive" });
      return;
    }
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !result) return;

    setIsRendering(true);
    toast({ title: "렌더링 시작", description: "쇼츠 자동 생성을 시작합니다. (약 1~3분 소요)" });

    try {
      const blob = await renderShort(file, result);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "short_final.mp4";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast({ title: "렌더링 완료", description: "최종 영상 다운로드가 완료되었습니다." });
    } catch (error: any) {
      toast({ title: "렌더링 실패", description: error.message, variant: "destructive" });
    } finally {
      setIsRendering(false);
      e.target.value = ''; // Reset file input
    }
  };

  return (
    <div className="space-y-6 pt-4 bg-[#1a1a2e] rounded-xl">
      <input 
        type="file" 
        hidden 
        ref={fileInputRef} 
        accept="video/*" 
        onChange={handleFileChange} 
      />
      
      <Button 
        onClick={handleRenderRequest}
        disabled={isRendering || !result}
        className="w-full h-16 bg-gradient-to-r from-[#8b5cf6] to-[#6d28d9] hover:from-[#7c3aed] hover:to-[#5b21b6] text-white text-xl font-black gap-4 shadow-2xl shadow-indigo-500/30 transition-all hover:scale-[1.01] active:scale-95 border-none"
      >
        {isRendering ? (
          <>
            <Loader2 className="w-7 h-7 animate-spin" />
            렌더링 중... (1~3분 소요)
          </>
        ) : (
          <>
            <Film className="w-7 h-7" />
            쇼츠 자동 생성 (딸깍!)
          </>
        )}
      </Button>

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
