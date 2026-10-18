import { Link } from "react-router-dom";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Code,
} from "../ui/StyleComponents";
import { segmentEvidence, splitPathToken } from "../../utils/investigateEvidence";

const CONFIDENCE_VARIANT = { low: "default", medium: "info", high: "success" };

function EvidenceItem({ text, reportId, findingIds }) {
  const pathPart = splitPathToken(text);
  const rest = pathPart ? pathPart.rest.replace(/^\s*[-—:]\s*/, "") : text;
  const segments = segmentEvidence(rest, findingIds);

  return (
    <li className="flex flex-wrap items-baseline gap-1.5 text-sm text-gray-300">
      {pathPart && <Code inline>{pathPart.path}</Code>}
      <span className="break-words">
        {segments.map((segment, index) =>
          segment.type === "finding" ? (
            <Link
              key={index}
              to={`/report/${reportId}/finding/${segment.findingId}`}
              className="text-cyan-400 underline underline-offset-2 rounded hover:text-cyan-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
            >
              {segment.value}
            </Link>
          ) : (
            <span key={index}>{segment.value}</span>
          )
        )}
      </span>
    </li>
  );
}

export function InvestigateReport({
  data,
  reportId,
  findingIds = [],
  currentLabel = null,
  onAgreeFp,
  isLabelPending = false,
}) {
  const { report, provider, model, usage } = data;
  const tokenTotal = (usage?.prompt_tokens || 0) + (usage?.completion_tokens || 0);
  const agreed = currentLabel === "false_positive";

  return (
    <section className="space-y-4" aria-label="Investigation report">
      <div className="flex items-center gap-2 flex-wrap">
        <Badge variant={CONFIDENCE_VARIANT[report.confidence] || "default"}>
          Confidence: {report.confidence}
        </Badge>
        {report.likely_false_positive && <Badge variant="warning">Likely false positive</Badge>}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Blast radius</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
            {report.summary}
          </p>
          {report.exploitability && (
            <div>
              <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">
                Exploitability
              </h4>
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                {report.exploitability}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Evidence</CardTitle>
        </CardHeader>
        <CardContent>
          {report.evidence?.length ? (
            <ul className="space-y-2">
              {report.evidence.map((item, index) => (
                <EvidenceItem key={index} text={item} reportId={reportId} findingIds={findingIds} />
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No evidence collected.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>False-positive indicators</CardTitle>
        </CardHeader>
        <CardContent>
          {report.false_positive_reasons?.length ? (
            <ul className="space-y-3">
              {report.false_positive_reasons.map((reason, index) => (
                <li key={index} className="flex items-start justify-between gap-3">
                  <span className="text-sm text-gray-300 leading-relaxed">{reason}</span>
                  {agreed ? (
                    <Badge variant="success" className="shrink-0">
                      Agreed
                    </Badge>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      className="shrink-0"
                      disabled={isLabelPending}
                      onClick={() => onAgreeFp?.()}
                    >
                      Agree — mark false positive
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No false-positive indicators identified.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recommended actions</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
            {report.fix_guidance}
          </p>
        </CardContent>
      </Card>

      <p className="text-xs text-gray-500 text-center">
        🤖 Investigation by{" "}
        <span className="text-cyan-400">
          {provider}/{model}
        </span>
        {` · ${tokenTotal} tokens`}
      </p>
    </section>
  );
}
