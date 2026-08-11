import type { StudentReportQuestion } from "../../lib/analytics";

type Props = {
  questions: StudentReportQuestion[];
};

/** Resolve a letter (A/B/C/D) to its option text */
function optionText(q: StudentReportQuestion, letter: string | null): string {
  if (!letter) return "—";
  const map: Record<string, string | null | undefined> = {
    A: q.option_a,
    B: q.option_b,
    C: q.option_c,
    D: q.option_d,
  };
  const text = map[letter];
  return text ? `${letter}. ${text}` : letter;
}

export function QuestionAnalysisTable({ questions }: Props) {
  if (questions.length === 0) {
    return (
      <p className="text-sm text-slate-500">No question data available for this attempt.</p>
    );
  }

  return (
    <div className="question-analysis">
      {/* Desktop table */}
      <div className="hidden md:block">
        <table className="w-full text-left text-sm question-table" style={{ tableLayout: "fixed" }}>
          <colgroup>
            <col style={{ width: "4%" }} />
            <col style={{ width: "24%" }} />
            <col style={{ width: "14%" }} />
            <col style={{ width: "21%" }} />
            <col style={{ width: "21%" }} />
            <col style={{ width: "8%" }} />
            <col style={{ width: "8%" }} />
          </colgroup>
          <thead>
            <tr>
              <th className="px-2 py-2.5 text-xs font-semibold text-slate-600 bg-slate-50 rounded-tl-md">
                Q#
              </th>
              <th className="px-3 py-2.5 text-xs font-semibold text-slate-600 bg-slate-50">
                Question
              </th>
              <th className="px-2 py-2.5 text-xs font-semibold text-slate-600 bg-slate-50">
                Domain
              </th>
              <th className="px-2 py-2.5 text-xs font-semibold text-slate-600 bg-slate-50">
                Your Answer
              </th>
              <th className="px-2 py-2.5 text-xs font-semibold text-slate-600 bg-slate-50">
                Correct Answer
              </th>
              <th className="px-2 py-2.5 text-xs font-semibold text-slate-600 bg-slate-50 text-center">
                % Right
              </th>
              <th className="px-2 py-2.5 text-xs font-semibold text-slate-600 bg-slate-50 text-center rounded-tr-md">
                Result
              </th>
            </tr>
          </thead>
          <tbody>
            {questions.map((q, idx) => (
              <tr
                key={q.question_number}
                className={`border-t border-slate-100 ${idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"}`}
              >
                <td className="px-2 py-2 font-semibold text-slate-800">{q.question_number}</td>
                <td className="px-3 py-2 text-slate-700 leading-relaxed" style={{ wordWrap: "break-word", overflowWrap: "break-word" }}>
                  {q.question_text ?? "—"}
                </td>
                <td className="px-2 py-2">
                  <DomainBadge domain={q.domain} />
                </td>
                <td className="px-2 py-2">
                  <AnswerDisplay
                    text={optionText(q, q.detected_answer)}
                    isCorrect={q.is_correct}
                    isStudent
                  />
                </td>
                <td className="px-2 py-2">
                  <AnswerDisplay
                    text={optionText(q, q.correct_answer)}
                    isCorrect
                  />
                </td>
                <td className="px-2 py-2 text-center">
                  <PercentBadge percent={q.percent_correct} />
                </td>
                <td className="px-2 py-2 text-center">
                  <ResultBadge isCorrect={q.is_correct} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="space-y-3 md:hidden">
        {questions.map((q) => (
          <div key={q.question_number} className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-slate-800">Q{q.question_number}</span>
                <DomainBadge domain={q.domain} />
              </div>
              <ResultBadge isCorrect={q.is_correct} />
            </div>
            {q.question_text && (
              <p className="text-sm text-slate-600 mb-3 leading-relaxed">{q.question_text}</p>
            )}
            <div className="space-y-1 text-sm">
              <div className="flex gap-2">
                <span className="text-slate-500 shrink-0">Your:</span>
                <span className={q.is_correct ? "text-green-700" : "text-red-700"}>
                  {optionText(q, q.detected_answer)} {!q.is_correct && q.detected_answer ? "✗" : ""}
                </span>
              </div>
              <div className="flex gap-2">
                <span className="text-slate-500 shrink-0">Correct:</span>
                <span className="text-green-700">{optionText(q, q.correct_answer)}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-slate-500 shrink-0">Got right:</span>
                <span className="text-slate-700">{q.percent_correct.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DomainBadge({ domain }: { domain: string }) {
  return (
    <span className="inline-flex max-w-full items-center justify-center rounded-full bg-slate-100 px-2 py-0.5 text-center text-[11px] font-medium leading-tight text-slate-600 whitespace-normal break-words">
      {domain}
    </span>
  );
}

function AnswerDisplay({ text, isCorrect, isStudent }: { text: string; isCorrect?: boolean; isStudent?: boolean }) {
  if (text === "—") {
    return <span className="text-sm text-slate-400">—</span>;
  }
  return (
    <span className={`text-sm leading-relaxed ${isStudent && !isCorrect ? "text-red-700" : isStudent && isCorrect ? "text-green-700" : "text-green-700"}`}>
      {text}
      {isStudent && !isCorrect && <span className="ml-1 text-red-500">✗</span>}
    </span>
  );
}

function PercentBadge({ percent }: { percent: number | undefined }) {
  const val = percent ?? 0;
  const color =
    val >= 80 ? "text-green-700" :
    val >= 60 ? "text-blue-700" :
    val >= 40 ? "text-amber-700" :
    "text-red-600";
  return (
    <span className={`text-sm font-medium ${color}`}>
      {val.toFixed(0)}%
    </span>
  );
}

function ResultBadge({ isCorrect }: { isCorrect: boolean }) {
  if (isCorrect) {
    return (
      <span className="inline-flex items-center gap-0.5 rounded-full bg-green-100 px-2 py-0.5 text-[11px] font-semibold text-green-700">
        <CheckIcon /> Correct
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-0.5 rounded-full bg-red-100 px-2 py-0.5 text-[11px] font-semibold text-red-700">
      <CrossIcon /> Wrong
    </span>
  );
}

function CheckIcon() {
  return (
    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

function CrossIcon() {
  return (
    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}
