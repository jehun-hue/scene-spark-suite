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

const safeRender = (value: any): string => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  return JSON.stringify(value, null, 2);
};

const ResultPage = () => {
  const { result } = useAnalysisStore();
  const navigate = useNavigate();

  // Gemini 응답 구조가 매번 달라지므로 여러 경로에서 값을 탐색
  const deepGet = (obj: any, ...paths: string[]): any => {
    for (const path of paths) {
      let val = obj;
      for (const key of path.split('.')) {
        val = val?.[key];
        if (val === undefined || val === null) break;
      }
      if (val !== undefined && val !== null) return val;
    }
    return null;
  };

  const vd = deepGet(result, 'viral_dashboard', 'viral_probability_dashboard', 'analysis_metadata.viral_dashboard', '🎯 바이럴 확률 대시보드 (v2.1)', '바이럴_확률_대시보드');
  const safetyChannel = result?.['channel_safety'] || result?.['채널 안전'] || deepGet(result, 'safety.channel_safety', 'safety.채널_안전');
  const safetyRevenue = result?.['revenue_risk'] || result?.['profit_risk'] || result?.['수익 리스크'] || deepGet(result, 'safety.revenue_risk', 'safety.수익_리스크');
  const targetData = deepGet(result, 'target', 'target_settings', '타겟 설정');
  const deepDive = deepGet(result, 'deep_dive_report', '심층 조사 보고서');
  const productionData = deepGet(result, 'production', 'final_production_blueprint', '최종_프로덕션_블루프린트');
  const editMap = deepGet(result, 'edit_map', 'edit_engineering', '편집_설계');
  const edl = deepGet(result, 'edit_decision_list', 'edit_map.edit_decision_list', 'edit_engineering.edit_decision_list', 'edit_engineering.edl') || [];
  const emotionalVar = deepGet(result, 'emotional_variations', '감정_변주');
  const searchKw = deepGet(result, 'additional_video_source_keywords', 'search_keywords', 'supplementary_assets', '검색_키워드', '추가_영상_소스_검색_키워드');
  const finalScript = deepGet(result, 'final_production_blueprint.final_script', 'production.final_script', '최종_대본');
  const emotionCurve = deepGet(result, 'final_production_blueprint.emotion_curve_design', 'final_production_blueprint.emotion_curve', 'production.emotion_curve', '감정_곡선') || [];
  const viralRec = deepGet(result, 'viral_probability_optimization_recommendation', 'viral_probability_optimization_recommendations', 'optimization_recommendation');
  const anchorTarget = deepGet(result, 'target.anchor_target', 'target.anchor', 'target_settings.anchor_target');
  const subTarget = deepGet(result, 'target.sub_target', 'target.sub', 'target_settings.sub_target');
  const timelineRatio = deepGet(result, 'timeline_ratio', 'edit_map.timeline_ratio', 'edit_engineering.timeline_ratio');
  const contentId = deepGet(result, 'content_id_analysis', 'edit_map.content_id_analysis');

  console.log("Analysis Result Keys:", result ? Object.keys(result) : "no result");
  console.log("Full Result:", JSON.stringify(result, null, 2).substring(0, 2000));

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

  // 제목 데이터 추출 로직
  const extractTitles = () => {
    if (!result) return [];
    const titles: { label: string; title: string; score: string }[] = [];
    const labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];

    // Path 1: final_production_blueprint.viral_titles (array of objects)
    const vt = result?.final_production_blueprint?.viral_titles
      || result?.production?.viral_titles
      || result?.viral_titles;

    if (Array.isArray(vt)) {
      vt.forEach((item: any, i: number) => {
        const t = typeof item === 'string' ? item : (item?.title || item?.제목 || item?.text || '');
        const s = typeof item === 'string' ? '' : (item?.score || item?.점수 || '');
        if (t) titles.push({ label: labels[i] || `#${i+1}`, title: t, score: String(s) });
      });
    }

    // Path 2: viral_titles as object with A_main, B_curiosity, C_search keys
    if (titles.length === 0 && vt && typeof vt === 'object' && !Array.isArray(vt)) {
      Object.entries(vt).forEach(([key, val]: [string, any], i: number) => {
        const t = typeof val === 'string' ? val : (val?.title || val?.제목 || val?.text || '');
        const s = typeof val === 'string' ? '' : (val?.score || val?.점수 || '');
        if (t) titles.push({ label: key, title: t, score: String(s) });
      });
    }

    // Path 3: root-level title keys (A_main, B_curiosity, C_search)
    if (titles.length === 0) {
      ['A_main', 'B_curiosity', 'C_search'].forEach((key) => {
        const val = result?.[key];
        if (val) {
          const t = typeof val === 'string' ? val : (val?.title || val?.제목 || '');
          const s = typeof val === 'string' ? '' : (val?.score || val?.점수 || '');
          if (t) titles.push({ label: key.split('_')[0], title: t, score: String(s) });
        }
      });
    }

    // Path 4: production.titles.top_7
    if (titles.length === 0) {
      const top7 = result?.production?.titles?.top_7 || result?.final_production_blueprint?.titles?.top_7;
      if (Array.isArray(top7)) {
        top7.forEach((item: any, i: number) => {
          const t = typeof item === 'string' ? item : (item?.title || item?.제목 || '');
          if (t) titles.push({ label: labels[i] || `#${i+1}`, title: t, score: '' });
        });
      }
    }

    // Path 5: emotional_variations titles
    if (Array.isArray(emotionalVar)) {
      emotionalVar.forEach((v: any) => {
        const driver = v?.emotion_driver || v?.감정_드라이버 || '';
        const vTitles = v?.viral_titles || v?.titles;
        if (Array.isArray(vTitles)) {
          vTitles.forEach((item: any, i: number) => {
            const t = typeof item === 'string' ? item : (item?.title || item?.제목 || '');
            const s = typeof item === 'string' ? '' : (item?.score || item?.점수 || '');
            if (t) titles.push({ label: `[${driver}] ${labels[i] || ''}`, title: t, score: String(s) });
          });
        }
      });
    }

    return titles;
  };

  return (
    <div className="space-y-6">
      <StepProgress current={1} />
      
      {/* 바이럴 대시보드 */}
      {vd && (
        <div className="bg-gray-900 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">🎯 바이럴 확률 대시보드</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded p-3">
              <p className="text-xs text-gray-400">소재 잠재력</p>
              <p className="text-lg font-bold text-red-400">{safeRender(vd?.['소재_잠재력'] || vd?.material_potential || vd?.['material_potential'] || '-')}</p>
            </div>
            <div className="bg-gray-800 rounded p-3">
              <p className="text-xs text-gray-400">첫 인상 파워</p>
              <p className="text-lg font-bold">{safeRender(vd?.['첫_인상_파워'] || vd?.first_impression_power || vd?.['first_impression_power'] || '-')}</p>
            </div>
            <div className="bg-gray-800 rounded p-3">
              <p className="text-xs text-gray-400">종합 등급</p>
              <p className="text-lg font-bold text-red-400">{safeRender(vd?.['종합_등급'] || vd?.overall_grade || vd?.['overall_grade'] || '-')}</p>
            </div>
            <div className="bg-gray-800 rounded p-3">
              <p className="text-xs text-gray-400">루프 연결</p>
              <p className="text-lg font-bold">{safeRender(vd?.['루프_연결'] || vd?.loop_connection || vd?.['loop_connection'] || '-')}</p>
            </div>
          </div>
          {viralRec && (
            <p className="text-yellow-400 text-sm mt-4">💡 최적화 권고: {safeRender(viralRec)}</p>
          )}
        </div>
      )}

      {/* 안전 검증 */}
      {(safetyChannel || safetyRevenue) && (
        <div className="bg-[#1a1a2e] rounded-xl p-6 flex gap-4">
          <div className="bg-[#2a2a40] rounded-lg p-4 flex-1">
            <p className="text-gray-400 text-xs">채널 안전</p>
            <p className="text-lg font-bold text-white">{safeRender(safetyChannel || '-')}</p>
          </div>
          <div className="bg-[#2a2a40] rounded-lg p-4 flex-1">
            <p className="text-gray-400 text-xs">수익 리스크</p>
            <p className="text-lg font-bold text-white">{safeRender(safetyRevenue || '-')}</p>
          </div>
        </div>
      )}

      {/* 타겟 분석 */}
      {targetData && (
        <div className="bg-gray-900 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">🎯 타겟 분석</h2>
          {targetData.status === '미설정' ? (
            <p className="text-yellow-400">{safeRender(targetData.prompt || '앵커 타겟이 설정되지 않았습니다.')}</p>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded p-3">
                <p className="text-xs text-gray-400">앵커 타겟</p>
                <p className="font-bold">{safeRender(anchorTarget?.target_name || anchorTarget?.name || '-')}</p>
                <p className="text-sm text-gray-300">{safeRender(anchorTarget?.core_identity || anchorTarget?.identity || '-')}</p>
              </div>
              <div className="bg-gray-800 rounded p-3">
                <p className="text-xs text-gray-400">서브 타겟</p>
                <p className="text-sm text-gray-300">
                  {safeRender(typeof subTarget === 'string' ? subTarget : subTarget?.inferred_name || subTarget?.name || '-')}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  톤: {safeRender(anchorTarget?.tone_and_manner || anchorTarget?.tone || targetData.tone || '-')}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 제목 후보 */}
      <TitleCandidates data={extractTitles()} />

      <ExportButtons />
      <TimelineBar data={timelineRatio} />
      <ContentIdCards data={contentId} />

      {/* 최종 대본 */}
      {finalScript && (
        <div className="bg-[#1a1a2e] rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">🎤 최종 대본</h2>
          <pre className="text-gray-200 text-sm whitespace-pre-wrap bg-[#2a2a40] rounded-lg p-4 leading-relaxed">{safeRender(finalScript)}</pre>
        </div>
      )}

      {/* 감정 곡선 */}
      {Array.isArray(emotionCurve) && emotionCurve.length > 0 && (
        <div className="bg-[#1a1a2e] rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">📈 감정 곡선</h2>
          <div className="grid gap-4">
            {emotionCurve.map((seg: any, i: number) => {
              const time = seg?.time || seg?.시간 || seg?.time_range || seg?.구간 || '';
              const emotion = seg?.emotion || seg?.감정 || seg?.target_emotion || '';
              const intensity = seg?.intensity || seg?.강도 || seg?.level || '';
              return (
                <div key={i} className="bg-[#2a2a40] rounded-lg p-3 flex items-center gap-4">
                  <span className="text-purple-400 font-mono text-xs w-20">{safeRender(time)}</span>
                  <span className="text-white font-bold text-sm flex-1">{safeRender(emotion)}</span>
                  <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-400 to-red-400 rounded-full"
                      style={{ width: `${(Number(String(intensity).replace(/[^0-9]/g,'')) || 0) * 10}%` }}
                    />
                  </div>
                  <span className="text-yellow-400 font-black text-sm w-12 text-right">{safeRender(intensity)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {/* 장면별 대본 구성 */}
      <div className="bg-[#1a1a2e] rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4">🎬 장면별 대본 구성</h2>
        {Array.isArray(edl) && edl.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#2a2a40] text-gray-400 text-xs uppercase tracking-wider">
                  <th className="p-3 border border-gray-700">시간</th>
                  <th className="p-3 border border-gray-700">편집 이벤트</th>
                  <th className="p-3 border border-gray-700">대본 싱크</th>
                  <th className="p-3 border border-gray-700">자막</th>
                  <th className="p-3 border border-gray-700">오디오</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {edl.map((item: any, i: number) => (
                  <tr key={i} className="border-b border-gray-800 hover:bg-white/5 transition-colors">
                    <td className="p-3 border border-gray-800 text-blue-400 font-mono whitespace-nowrap">
                      {safeRender(item?.timecode || item?.time || item?.시간 || item?.timestamp || '-')}
                    </td>
                    <td className="p-3 border border-gray-800 text-white">
                      {safeRender(item?.edit_event || item?.편집_이벤트 || item?.event || item?.effect || '-')}
                    </td>
                    <td className="p-3 border border-gray-800 text-gray-400">
                      {safeRender(item?.script_sync || item?.대본_싱크 || item?.script || item?.narration || '-')}
                    </td>
                    <td className="p-3 border border-gray-800 text-yellow-400">
                      {safeRender(item?.subtitle || item?.자막 || item?.caption || '-')}
                    </td>
                    <td className="p-3 border border-gray-800 text-gray-500">
                      {safeRender(item?.audio || item?.오디오 || item?.sound || '-')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-sm italic">편집점 데이터 없음</p>
        )}
      </div>

      {/* 심층 조사 보고서 */}
      {deepDive && (
        <div className="bg-[#1a1a2e] rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">🔍 심층 조사 보고서</h2>
          <div className="space-y-4">
            {Object.entries(deepDive).map(([key, value]: [string, any]) => (
              <div key={key} className="bg-[#2a2a40] rounded-lg p-4">
                <h3 className="text-yellow-400 font-bold mb-2">{safeRender(key)}</h3>
                <div className="text-gray-300 text-sm whitespace-pre-wrap">
                  {typeof value === 'string' ? value
                    : Array.isArray(value) ? (
                      <ul className="list-disc list-inside space-y-1">
                        {value.map((item: any, i: number) => (
                          <li key={i}>
                            {typeof item === 'string' ? item
                              : item.criticism ? <><strong>반론:</strong> {item.criticism}<br/><strong>방어:</strong> {item.defense}</>
                              : item.video_expression ? <><strong>{item.video_expression}</strong> → {item.accurate_name}: {item.description}</>
                              : safeRender(item)
                            }
                          </li>
                        ))}
                      </ul>
                    )
                    : value && typeof value === 'object' && value.pros ? (
                      <div>
                        <p className="text-green-400 font-semibold mb-1">장점:</p>
                        <ul className="list-disc list-inside space-y-1 mb-2">
                          {(value.pros || []).map((p: string, i: number) => <li key={i}>{p}</li>)}
                        </ul>
                        <p className="text-red-400 font-semibold mb-1">단점:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {(value.cons || []).map((c: string, i: number) => <li key={i}>{c}</li>)}
                        </ul>
                      </div>
                    )
                    : safeRender(value)
                  }
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 감정 변주 */}
      {emotionalVar && (
        <div className="bg-[#1a1a2e] rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">🎭 감정 변주 대본</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(emotionalVar).map(([key, value]: [string, any]) => (
              <div key={key} className="bg-[#2a2a40] rounded-lg p-4">
                <p className="text-yellow-400 font-bold text-sm mb-2">
                  {key === 'greed' ? '💰 물욕' : key === 'instinct' ? '🔥 본능' : key === 'emotion' ? '💗 감동' : key === 'anger' ? '😡 분노' : safeRender(key)}
                </p>
                <div className="text-gray-300 text-sm whitespace-pre-wrap">{safeRender(value?.full_text || value)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 검색 키워드 */}
      {searchKw && (
        <div className="bg-gray-900 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4"># 검색 키워드</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm text-gray-400 mb-2">한국어 키워드</h3>
              <div className="flex flex-wrap gap-2">
                {Array.isArray(searchKw) 
                  ? searchKw.map((kw: any, i: number) => (
                      <span key={i} className="bg-purple-900/50 text-purple-300 px-3 py-1 rounded-full text-sm">
                        {safeRender(kw['한국어'] || kw.korean || kw)}
                      </span>
                    ))
                  : (searchKw?.['한국어'] || searchKw?.korean || []).map((kw: any, i: number) => (
                      <span key={i} className="bg-purple-900/50 text-purple-300 px-3 py-1 rounded-full text-sm">
                        {safeRender(kw)}
                      </span>
                    ))
                }
              </div>
            </div>
            <div>
              <h3 className="text-sm text-gray-400 mb-2">English Keywords</h3>
              <div className="flex flex-wrap gap-2">
                {Array.isArray(searchKw)
                  ? searchKw.map((kw: any, i: number) => (
                      <span key={i} className="bg-blue-900/50 text-blue-300 px-3 py-1 rounded-full text-sm">
                        {safeRender(kw['영어'] || kw.english || kw)}
                      </span>
                    ))
                  : (searchKw?.['영어'] || searchKw?.english || []).map((kw: any, i: number) => (
                      <span key={i} className="bg-blue-900/50 text-blue-300 px-3 py-1 rounded-full text-sm">
                        {safeRender(kw)}
                      </span>
                    ))
                }
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 원본 JSON 디버그 (개발용) */}
      <details className="bg-[#1a1a2e] rounded-xl p-4">
        <summary className="text-gray-500 cursor-pointer text-sm">📋 원본 JSON 데이터 보기 (디버그)</summary>
        <pre className="text-gray-400 text-xs mt-4 overflow-auto max-h-96 whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
      </details>
    </div>
  );


};


export default ResultPage;
