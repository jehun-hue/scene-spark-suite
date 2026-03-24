import StepProgress from "@/components/StepProgress";
import TitleCandidates from "@/components/result/TitleCandidates";
import ExportButtons from "@/components/result/ExportButtons";
import TimelineBar from "@/components/result/TimelineBar";
import ContentIdCards from "@/components/result/ContentIdCards";
import ScriptTable from "@/components/result/ScriptTable";

const ResultPage = () => {
  return (
    <div className="space-y-6">
      <StepProgress current={1} />
      <TitleCandidates />
      <ExportButtons />
      <TimelineBar />
      <ContentIdCards />
      <ScriptTable />
    </div>
  );
};

export default ResultPage;
