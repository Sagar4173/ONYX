import { Badge, Modal } from "../ui/StyleComponents";

export const CitationPanel = ({ isOpen, onClose, n, citation }) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    size="xl"
    title={citation?.header ? `Citation [${n}] — ${citation.header}` : `Citation [${n}]`}
  >
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {citation?.source_id && <Badge variant="info">{citation.source_id}</Badge>}
        {citation?.cwe_id && <Badge variant="warning">{citation.cwe_id}</Badge>}
        {citation?.source && <Badge>{citation.source}</Badge>}
      </div>
      <p className="text-sm text-gray-300 whitespace-pre-wrap">
        {citation?.text || "No source text available."}
      </p>
    </div>
  </Modal>
);
