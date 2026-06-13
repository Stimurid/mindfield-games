const STAGE_LABEL = ["сырьё", "упражнение", "игра-упр.", "психотех.", "коэволюц.", "школа"];
const STAGE_COLOR = ["#888", "#a78", "#7a8", "#7aa", "#aa7", "#a78"];

export default function MaturityBadge({ stage }: { stage: number | null | undefined }) {
  if (stage === null || stage === undefined) {
    return <span className="kbd" style={{ background: "rgba(120,120,120,0.2)" }}>?</span>;
  }
  return (
    <span
      className="kbd"
      title={`стадия ${stage} · ${STAGE_LABEL[stage]}`}
      style={{ background: `${STAGE_COLOR[stage]}33`, color: STAGE_COLOR[stage] }}
    >
      {stage} · {STAGE_LABEL[stage]}
    </span>
  );
}
