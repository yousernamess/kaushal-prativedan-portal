import { useState } from "react";
import type { QuestionItem } from "../../lib/analytics";
import { QuestionHistory } from "./question-history";

type Props = {
  assessmentId: number;
  questions: QuestionItem[];
  schoolId: number | null;
  classNumber: number | null;
  section: string | null;
};

export function QuestionTable({ assessmentId, questions, schoolId, classNumber, section }: Props) {
  const [expandedQuestionId, setExpandedQuestionId] = useState<number | null>(null);

  if (questions.length === 0) {
    return <p className="text-sm text-slate-500">No questions available for this assessment.</p>;
  }

  return (
    <div className="space-y-2">
      {/* Desktop table */}
      <div className="hidden overflow-x-auto rounded-lg border bg-white md:block">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Q#</th>
              <th className="px-4 py-3 font-medium">Question</th>
              <th className="px-4 py-3 font-medium">Domain</th>
              <th className="px-4 py-3 font-medium text-center">Assessed</th>
              <th className="px-4 py-3 font-medium text-center">Correct</th>
              <th className="px-4 py-3 font-medium text-center">Wrong</th>
              <th className="px-4 py-3 font-medium text-center">% Correct</th>
            </tr>
          </thead>
          <tbody>
            {questions.map((q) => (
              <QuestionRow
                key={q.question_id}
                question={q}
                isExpanded={expandedQuestionId === q.question_id}
                onToggle={() => setExpandedQuestionId(expandedQuestionId === q.question_id ? null : q.question_id)}
                assessmentId={assessmentId}
                schoolId={schoolId}
                classNumber={classNumber}
                section={section}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="space-y-2 md:hidden">
        {questions.map((q) => (
          <div key={q.question_id} className="rounded-lg border bg-white shadow-sm">
            <button
              className="w-full p-3 text-left"
              onClick={() => setExpandedQuestionId(expandedQuestionId === q.question_id ? null : q.question_id)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">Q{q.question_number}</span>
                    <DomainBadge domain={q.domain} />
                  </div>
                  {q.question_text && (
                    <p className="mt-1 text-sm text-slate-600 line-clamp-2">{q.question_text}</p>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <PercentageBadge percentage={q.percentage} />
                  <p className="mt-0.5 text-xs text-slate-500">{q.correct}/{q.assessed}</p>
                </div>
              </div>
              {/* Progress bar */}
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-blue-600"
                  style={{ width: `${Math.min(q.percentage, 100)}%` }}
                />
              </div>
            </button>

            {/* Expanded history */}
            {expandedQuestionId === q.question_id && (
              <div className="border-t px-3 py-3">
                <QuestionHistory
                  assessmentId={assessmentId}
                  questionId={q.question_id}
                  schoolId={schoolId}
                  classNumber={classNumber}
                  section={section}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function QuestionRow({
  question: q, isExpanded, onToggle, assessmentId, schoolId, classNumber, section,
}: {
  question: QuestionItem;
  isExpanded: boolean;
  onToggle: () => void;
  assessmentId: number;
  schoolId: number | null;
  classNumber: number | null;
  section: string | null;
}) {
  return (
    <>
      <tr
        className="cursor-pointer border-t transition-colors hover:bg-slate-50"
        onClick={onToggle}
      >
        <td className="px-4 py-3 font-medium text-slate-900">Q{q.question_number}</td>
        <td className="max-w-[300px] truncate px-4 py-3 text-slate-700">
          {q.question_text ?? "—"}
        </td>
        <td className="px-4 py-3"><DomainBadge domain={q.domain} /></td>
        <td className="px-4 py-3 text-center text-slate-700">{q.assessed}</td>
        <td className="px-4 py-3 text-center text-green-700 font-medium">{q.correct}</td>
        <td className="px-4 py-3 text-center text-red-600">{q.wrong}</td>
        <td className="px-4 py-3 text-center">
          <PercentageBadge percentage={q.percentage} />
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={7} className="border-t bg-slate-50 px-4 py-4">
            <QuestionHistory
              assessmentId={assessmentId}
              questionId={q.question_id}
              schoolId={schoolId}
              classNumber={classNumber}
              section={section}
            />
          </td>
        </tr>
      )}
    </>
  );
}

function DomainBadge({ domain }: { domain: string }) {
  return (
    <span className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
      {domain}
    </span>
  );
}

function PercentageBadge({ percentage }: { percentage: number }) {
  const color =
    percentage >= 80 ? "bg-green-100 text-green-700" :
    percentage >= 60 ? "bg-blue-100 text-blue-700" :
    percentage >= 40 ? "bg-amber-100 text-amber-700" :
    "bg-red-100 text-red-700";

  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${color}`}>
      {percentage.toFixed(1)}%
    </span>
  );
}
