const steps = [
  "프로젝트", "채널/영상 분석", "대본", "사운드", "이미지/영상", "편집실", "업로드"
];

const StepProgress = ({ current = 0 }: { current?: number }) => {
  return (
    <div className="flex items-center gap-1 mb-8">
      {steps.map((step, i) => (
        <div key={step} className="flex items-center gap-1">
          <div className="flex items-center gap-2">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${
                i <= current
                  ? "gradient-primary text-primary-foreground"
                  : "bg-secondary text-muted-foreground"
              }`}
            >
              {i + 1}
            </div>
            <span className={`text-xs whitespace-nowrap ${
              i <= current ? "text-foreground" : "text-muted-foreground"
            }`}>
              {step}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className={`w-6 h-px mx-1 ${
              i < current ? "bg-primary" : "bg-border"
            }`} />
          )}
        </div>
      ))}
    </div>
  );
};

export default StepProgress;
