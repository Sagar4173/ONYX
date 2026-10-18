import { FixDiffViewer } from "../components/reports/FixDiffViewer";

const TYPICAL_DIFF = [
  "--- a/src/api/orders.py",
  "+++ b/src/api/orders.py",
  "@@ -84,7 +84,8 @@ def get_order(order_id):",
  "     conn = get_connection()",
  "     cursor = conn.cursor()",
  '-    query = f"SELECT * FROM orders WHERE id={order_id}"',
  "-    cursor.execute(query)",
  '+    query = "SELECT * FROM orders WHERE id=%s"',
  "+    cursor.execute(query, (order_id,))",
  "     rows = cursor.fetchall()",
  "     return rows",
].join("\n");

const MANY_HUNKS_DIFF = [
  "--- a/src/core/engine.py",
  "+++ b/src/core/engine.py",
  ...Array.from({ length: 15 }, (_, i) => [
    `@@ -${i * 10 + 1},2 +${i * 10 + 1},2 @@`,
    ` ctx line before ${i}`,
    `-risky_call_${i}()`,
    `+safe_call_${i}()`,
  ]).flat(),
].join("\n");

export default {
  title: "AI/FixDiffViewer",
  component: FixDiffViewer,
  decorators: [
    (Story) => (
      <div className="max-w-3xl bg-gray-900 p-6">
        <Story />
      </div>
    ),
  ],
};

export const Typical = {
  args: { diff: TYPICAL_DIFF },
};

export const Truncated = {
  args: { diff: MANY_HUNKS_DIFF, maxHunks: 12 },
};

export const NoChanges = {
  args: { diff: "" },
};
