import { Upload, FileVideo } from "lucide-react";
import { Button } from "@/components/ui/button";
import StepProgress from "@/components/StepProgress";
import { useNavigate } from "react-router-dom";

const UploadPage = () => {
  const navigate = useNavigate();

  return (
    <div className="max-w-3xl mx-auto">
      <StepProgress current={0} />

      <div className="border-2 border-dashed border-border rounded-xl p-16 flex flex-col items-center justify-center text-center hover:border-primary/50 transition-colors cursor-pointer group">
        <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
          <FileVideo className="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" />
        </div>
        <p className="text-foreground font-medium mb-2">영상 파일을 드래그하거나 클릭하여 업로드</p>
        <p className="text-sm text-muted-foreground mb-1">지원 포맷: MP4, MOV, AVI</p>
        <p className="text-xs text-muted-foreground">최대 2GB</p>
      </div>

      <div className="flex justify-center mt-8">
        <Button
          size="lg"
          className="gradient-primary gradient-primary-hover text-primary-foreground px-12 py-6 text-base font-semibold glow-primary animate-pulse-glow"
          onClick={() => navigate("/result")}
        >
          <Upload className="w-5 h-5 mr-2" />
          분석 시작
        </Button>
      </div>
    </div>
  );
};

export default UploadPage;
