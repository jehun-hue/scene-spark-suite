import { useState } from "react";
import { Upload, FileVideo, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import StepProgress from "@/components/StepProgress";
import { useNavigate } from "react-router-dom";
import { useAnalysisStore } from "@/stores/analysisStore";
import { analyzeVideo } from "@/services/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const UploadPage = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  
  const { isLoading, error, setLoading, setResult, setError } = useAnalysisStore();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert("분석할 파일을 선택해주세요.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await analyzeVideo(file);
      setResult(data);
      navigate("/result");
    } catch (err: any) {
      setError(err.message || "영상 분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <StepProgress current={0} />

      <label className="block">
        <div className={`border-2 border-dashed rounded-xl p-16 flex flex-col items-center justify-center text-center transition-colors cursor-pointer group ${file ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}`}>
          <input type="file" className="hidden" accept="video/*" onChange={handleFileChange} disabled={isLoading} />
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 transition-colors ${file ? 'bg-primary/20 text-primary' : 'bg-secondary text-muted-foreground group-hover:text-primary group-hover:bg-primary/20'}`}>
            <FileVideo className="w-8 h-8" />
          </div>
          <p className="text-foreground font-medium mb-2">
            {file ? file.name : "영상 파일을 드래그하거나 클릭하여 업로드"}
          </p>
          <p className="text-sm text-muted-foreground mb-1">지원 포맷: MP4, MOV, AVI</p>
          <p className="text-xs text-muted-foreground">최대 2GB</p>
        </div>
      </label>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex justify-center">
        <Button
          size="lg"
          className="gradient-primary gradient-primary-hover text-primary-foreground px-12 py-6 text-base font-semibold glow-primary"
          onClick={handleUpload}
          disabled={!file || isLoading}
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
          ) : (
            <Upload className="w-5 h-5 mr-2" />
          )}
          {isLoading ? "분석 중..." : "분석 시작"}
        </Button>
      </div>
    </div>
  );
};

export default UploadPage;
