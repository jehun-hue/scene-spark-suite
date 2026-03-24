import StepProgress from "@/components/StepProgress";
import TitleCandidates from "@/components/result/TitleCandidates";
import ExportButtons from "@/components/result/ExportButtons";
import TimelineBar from "@/components/result/TimelineBar";
import ContentIdCards from "@/components/result/ContentIdCards";
import ScriptTable from "@/components/result/ScriptTable";
import { useAnalysisStore } from "@/stores/analysisStore";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Upload } from "lucide-react";

const ResultPage = () => {
  const { result } = useAnalysisStore();
  const navigate = useNavigate();

  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center space-y-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold">분석 결과가 없습니다</h2>
          <p className="text-muted-foreground text-sm">먼저 영상을 업로드하여 분석을 진행해주세요.</p>
        </div>
        <Button onClick={() => navigate("/upload")} className="gradient-primary text-white">
          <Upload className="w-4 h-4 mr-2" />
          영상 업로드하러 가기
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <StepProgress current={1} />
      <TitleCandidates data={result?.production?.titles?.top_7} />
      <ExportButtons />
      <TimelineBar data={result?.timeline_ratio} />
      <ContentIdCards data={result?.content_id_analysis} />
      <ScriptTable data={result?.edit_map?.edit_decision_list} />
    </div>
  );
};

export default ResultPage;
