import type { GameGenome, GameSession, Material } from "../types";
import RoundHeader from "./RoundHeader";
import LLMPanel from "./LLMPanel";
import TracePanel from "./TracePanel";
import ExportTraceButton from "./ExportTraceButton";
import ClickableTextUnits from "./fields/ClickableTextUnits";
import GapClickText from "./fields/GapClickText";
import CardSorting from "./fields/CardSorting";
import MediumShiftPhrase from "./fields/MediumShiftPhrase";
import PromiseCourtText from "./fields/PromiseCourtText";

interface Props {
  genome: GameGenome;
  material: Material;
  session: GameSession;
  onChange: (s: GameSession) => void;
}

export default function GameShell(props: Props) {
  const { genome } = props;
  const FieldComp =
    genome.field_type === "clickable_text_units" ? ClickableTextUnits
    : genome.field_type === "gap_click_text" ? GapClickText
    : genome.field_type === "card_sorting" ? CardSorting
    : genome.field_type === "promise_court_text" ? PromiseCourtText
    : MediumShiftPhrase;

  return (
    <div className="shell-grid">
      <RoundHeader genome={genome} session={props.session} />
      <div className="field-panel">
        <FieldComp {...props} />
      </div>
      <div className="side-col">
        <LLMPanel genome={genome} session={props.session} />
        <TracePanel session={props.session} />
        <ExportTraceButton session={props.session} />
      </div>
    </div>
  );
}
