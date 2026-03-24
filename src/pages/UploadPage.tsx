import { useState, useRef, useEffect } from "react";
import { 
  Upload, Search, FileText, Type, Scissors, Heart, Hash, 
  Loader2, AlertCircle, CheckCircle2, XCircle, Play
} from "lucide-react";
import { Button } from "@/components/ui/button";
import StepProgress from "@/components/StepProgress";
import { useNavigate } from "react-router-dom";
import { useAnalysisStore } from "@/stores/analysisStore";
import { 
  stepUpload, stepAnalyze, stepScript, stepTitles, 
  stepEditpoints, stepVariations, stepKeywords 
} from "@/services/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const STEPS = [
  { id: 1, name: "영상 업로드", icon: Upload },
  { id: 2, name: "기본 분석", icon: Search },
  { id: 3, name: "대본 작성", icon: FileText },
  { id: 4, name: "제목 생성", icon: Type },
  { id: 5, name: "편집점 설계", icon: Scissors },
  { id: 6, name: "감정 변주", icon: Heart },
  { id: 7, name: "키워드 생성", icon: Hash },
];

const UploadPage = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 1 to 7
  const [stepStatus, setStepStatus] = useState<Record<number, 'waiting' | 'running' | 'complete' | 'error'>>({
    1: 'waiting', 2: 'waiting', 3: 'waiting', 4: 'waiting', 5: 'waiting', 6: 'waiting', 7: 'waiting'
  });
  const [stepTime, setStepTime] = useState<Record<number, number>>({});
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<any>(null);

  useEffect(() => {
    if (isLoading && currentStep > 0 && stepStatus[currentStep] === 'running') {
      const start = Date.now();
      timerRef.current = setInterval(() => {
        setStepTime(prev => ({
          ...prev,
          [currentStep]: Math.floor((Date.now() - start) / 1000)
        }));
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isLoading, currentStep, stepStatus]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
    }
  };

  const updateStatus = (step: number, status: 'waiting' | 'running' | 'complete' | 'error') => {
    setStepStatus(prev => ({ ...prev, [step]: status }));
    if (status === 'running') setCurrentStep(step);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("분석할 파일을 먼저 선택해주세요.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setCurrentStep(1);
    
    let fileId = "";
    let analysisData = null;
    let scriptData = null;
    let titlesData = null;
    let editData = null;
    let variationsData = null;
    let keywordsData = null;
    let thumbnails = [];

    try {
      // Step 1: Upload
      updateStatus(1, 'running');
      const res1 = await stepUpload(selectedFile);
      if (res1.status === 'error') throw new Error(res1.message);
      fileId = res1.file_id;
      thumbnails = res1.thumbnails || [];
      updateStatus(1, 'complete');

      // Step 2: Analyze
      updateStatus(2, 'running');
      const res2 = await stepAnalyze(fileId);
      if (res2.status === 'error') throw new Error(res2.message);
      analysisData = res2.data;
      updateStatus(2, 'complete');

      // Step 3: Script
      updateStatus(3, 'running');
      const res3 = await stepScript(fileId, analysisData);
      if (res3.status === 'error') throw new Error(res3.message);
      scriptData = res3.data;
      updateStatus(3, 'complete');

      // Step 4: Titles
      updateStatus(4, 'running');
      const res4 = await stepTitles(fileId, analysisData, scriptData);
      if (res4.status === 'error') throw new Error(res4.message);
      titlesData = res4.data;
      updateStatus(4, 'complete');

      // Step 5: Editpoints
      updateStatus(5, 'running');
      const res5 = await stepEditpoints(fileId, scriptData);
      if (res5.status === 'error') throw new Error(res5.message);
      editData = res5.data;
      updateStatus(5, 'complete');

      // Step 6: Variations
      updateStatus(6, 'running');
      const res6 = await stepVariations(analysisData, scriptData);
      if (res6.status === 'error') throw new Error(res6.message);
      variationsData = res6.data;
      updateStatus(6, 'complete');

      // Step 7: Keywords
      updateStatus(7, 'running');
      const res7 = await stepKeywords(analysisData);
      if (res7.status === 'error') throw new Error(res7.message);
      keywordsData = res7.data;
      updateStatus(7, 'complete');

      // Merge Result
      const mergedResult = {
        ...analysisData,
        ...scriptData,
        ...titlesData,
        ...editData,
        ...variationsData,
        ...keywordsData,
        thumbnails
      };

      useAnalysisStore.getState().setResult(mergedResult);
      navigate("/result");

    } catch (err: any) {
      setError(err.message || "분석 중 오류가 발생했습니다.");
      updateStatus(currentStep || 1, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + ['Bytes', 'KB', 'MB', 'GB'][i];
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-20">
      <StepProgress current={0} />

      {!isLoading ? (
        <div 
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files?.[0]) {
              setSelectedFile(e.dataTransfer.files[0]);
              setError(null);
            }
          }}
          className={`border-2 border-dashed rounded-3xl p-16 flex flex-col items-center justify-center text-center transition-all cursor-pointer group 
            ${(selectedFile || isDragging) ? 'border-primary bg-primary/5 shadow-2xl shadow-primary/10' : 'border-border hover:border-primary/50'}
            ${isDragging ? 'scale-[1.02] border-primary' : ''}
          `}
        >
          <input type="file" ref={fileInputRef} className="hidden" accept="video/*" onChange={handleFileChange} />
          <div className={`w-20 h-20 rounded-3xl flex items-center justify-center mb-6 transition-all duration-500
            ${selectedFile ? 'bg-primary text-white rotate-12 scale-110' : 'bg-secondary text-muted-foreground group-hover:bg-primary/20 group-hover:text-primary'}
          `}>
            {selectedFile ? <Play className="w-10 h-10 fill-current" /> : <Upload className="w-10 h-10" />}
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold tracking-tight">
              {selectedFile ? selectedFile.name : "영상을 여기에 던져주세요"}
            </h2>
            {selectedFile && <p className="text-primary font-bold">{formatFileSize(selectedFile.size)}</p>}
            <p className="text-muted-foreground">MP4, MOV, AVI 최대 2GB 지원</p>
          </div>
        </div>
      ) : (
        <div className="bg-card/50 backdrop-blur-xl border border-border/50 rounded-3xl p-8 space-y-6 shadow-2xl">
          <div className="flex items-center justify-between pb-4 border-b border-border/50">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-primary" />
                AI 단계별 분석 진행 중
              </h2>
              <p className="text-sm text-muted-foreground">각 단계가 완료될 때마다 결과가 빌드됩니다.</p>
            </div>
            <div className="text-right">
              <span className="text-3xl font-black text-primary">{Math.round((currentStep / 7) * 100)}%</span>
            </div>
          </div>

          <div className="grid gap-3">
            {STEPS.map((step) => {
              const status = stepStatus[step.id];
              const isActive = currentStep === step.id;
              const isComplete = status === 'complete';
              const isError = status === 'error';
              const time = stepTime[step.id];

              return (
                <div key={step.id} className={`flex items-center gap-4 p-4 rounded-2xl border transition-all duration-500 ${
                  isActive ? 'bg-primary/10 border-primary shadow-lg scale-[1.02]' : 
                  isComplete ? 'bg-green-500/5 border-green-500/20 opacity-70' :
                  isError ? 'bg-red-500/5 border-red-500/20' : 'bg-secondary/20 border-transparent opacity-50'
                }`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    isActive ? 'bg-primary text-primary-foreground animate-pulse' :
                    isComplete ? 'bg-green-500 text-white' :
                    isError ? 'bg-red-500 text-white' : 'bg-secondary text-muted-foreground'
                  }`}>
                    <step.icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className={`font-bold ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                        {step.name}
                      </span>
                      {time !== undefined && <span className="text-xs font-mono text-muted-foreground">{time}s</span>}
                    </div>
                  </div>
                  {isComplete && <CheckCircle2 className="w-5 h-5 text-green-500" />}
                  {isError && <XCircle className="w-5 h-5 text-red-500" />}
                  {isActive && <Loader2 className="w-5 h-5 animate-spin text-primary" />}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {error && (
        <Alert variant="destructive" className="rounded-2xl border-2">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle className="font-bold">분석 중단됨</AlertTitle>
          <AlertDescription className="mt-2 flex items-center justify-between">
            <span>{error}</span>
            <Button size="sm" variant="outline" onClick={handleUpload} className="bg-white/10 hover:bg-white/20 border-0">재시도</Button>
          </AlertDescription>
        </Alert>
      )}

      <div className="flex justify-center">
        {!isLoading && (
          <Button
            size="lg"
            onClick={handleUpload}
            disabled={!selectedFile}
            className={`h-20 px-24 text-xl font-black rounded-3xl transition-all shadow-2xl group
              ${!selectedFile 
                ? 'bg-secondary text-muted-foreground' 
                : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:scale-105 active:scale-95 text-white shadow-purple-500/40'
              }
            `}
          >
            <Upload className="w-6 h-6 mr-3 group-hover:-translate-y-1 transition-transform" />
            무지성 분석 시작
          </Button>
        )}
      </div>
    </div>
  );
};

export default UploadPage;
