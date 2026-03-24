import { useState, useEffect } from "react";
import { Eye, EyeOff, Save, CheckCircle, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useSettingsStore } from "@/stores/settingsStore";
import { testApiKey } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

const SettingsPage = () => {
  const { apiKey, setApiKey } = useSettingsStore();
  const [keyInput, setKeyInput] = useState(apiKey);
  const [showKey, setShowKey] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const { toast } = useToast();

  const handleSave = () => {
    setApiKey(keyInput);
    toast({
      title: "저장 완료",
      description: "Gemini API 키가 성공적으로 저장되었습니다.",
      variant: "default",
    });
  };

  const handleTest = async () => {
    setIsTesting(true);
    try {
      await testApiKey(keyInput);
      toast({
        title: "테스트 성공",
        description: "API 키가 유효합니다.",
        variant: "default",
      });
    } catch (error: any) {
      toast({
        title: "테스트 실패",
        description: error.message || "API 키가 올바르지 않거나 다른 오류가 발생했습니다.",
        variant: "destructive",
      });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-10 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2.5 bg-indigo-500/10 rounded-xl">
          <Database className="w-6 h-6 text-indigo-400" />
        </div>
        <h1 className="text-3xl font-bold text-white tracking-tight">환경 설정</h1>
      </div>

      <Card className="bg-[#1a1a2e] border-none shadow-2xl ring-1 ring-white/5 overflow-hidden">
        <CardHeader className="pb-4">
          <CardTitle className="text-xl text-white">Gemini API 설정</CardTitle>
          <CardDescription className="text-gray-400">
            영상 분석에 사용할 Google Gemini API 키를 관리합니다. 
            키가 설정되지 않으면 서버의 기본 키를 활용합니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-bold text-gray-500 uppercase tracking-widest px-1">
              GEMINI API KEY
            </label>
            <div className="relative group">
              <Input
                type={showKey ? "text" : "password"}
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                placeholder="AIzaSy..."
                className="bg-[#2a2a40] border-none text-white h-14 pr-12 focus-visible:ring-indigo-500/50 rounded-xl transition-all"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
              >
                {showKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 pt-4">
            <Button
              onClick={handleSave}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white h-12 font-bold rounded-xl gap-2 shadow-lg shadow-indigo-500/20"
            >
              <Save className="w-4 h-4" />
              키 저장하기
            </Button>
            <Button
              onClick={handleTest}
              disabled={isTesting || !keyInput}
              variant="outline"
              className="flex-1 border-white/10 text-gray-300 hover:bg-white/5 h-12 font-bold rounded-xl gap-2"
            >
              {isTesting ? (
                <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent animate-spin rounded-full" />
              ) : (
                <CheckCircle className="w-4 h-4" />
              )}
              유효성 테스트
            </Button>
          </div>
        </CardContent>
      </Card>
      
      <div className="p-6 bg-yellow-500/5 border border-yellow-500/20 rounded-2xl flex gap-4 items-start">
        <div className="p-2 bg-yellow-500/10 rounded-lg shrink-0">
          <Eye className="w-5 h-5 text-yellow-500" />
        </div>
        <div className="space-y-1">
          <h4 className="font-bold text-yellow-500 text-sm">보안 유의사항</h4>
          <p className="text-xs text-gray-400 leading-relaxed">
            입력하신 API 키는 브라우저의 로컬 스토리지에만 저장되며, 외부로 유출되지 않습니다. 
            단, 공용 PC 사용 시 키 노출에 주의해 주시기 바랍니다.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
