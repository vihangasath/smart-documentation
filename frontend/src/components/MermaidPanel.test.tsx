import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { DiagramSetResponse } from "@/types/api";
import MermaidPanel from "./MermaidPanel";

vi.mock("next/dynamic", () => ({
  default: () =>
    function FakeDiagram({ chart }: { chart: string }) {
      return <pre data-testid="diagram">{chart}</pre>;
    },
}));

const downloadScaffold = vi.fn();
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, downloadScaffold: (...a: unknown[]) => downloadScaffold(...a) };
});

const data: DiagramSetResponse = {
  document_id: "d",
  all_valid: false,
  errors: ["Could not generate the architecture diagram: boom"],
  diagrams: [
    { id: "1", diagram_type: "er", title: "ER", mermaid_code: "erDiagram\nA ||--o{ B : x", is_valid: true, validation_errors: [] },
    { id: "2", diagram_type: "class", title: "Class", mermaid_code: "classDiagram\nclass A", is_valid: false, validation_errors: ["Unclosed brackets"] },
  ],
};

beforeEach(() => {
  downloadScaffold.mockReset();
});

describe("MermaidPanel", () => {
  it("shows the placeholder, then a spinner while processing", () => {
    const { rerender } = render(<MermaidPanel isProcessing={false} />);
    expect(screen.getByText(/Diagrams will appear here/)).toBeInTheDocument();
    rerender(<MermaidPanel isProcessing={true} />);
    expect(screen.getByText(/Generating architecture diagrams/)).toBeInTheDocument();
  });

  it("renders the first diagram and lets the user switch", async () => {
    render(<MermaidPanel isProcessing={false} data={data} />);
    expect(screen.getByTestId("diagram")).toHaveTextContent("erDiagram");

    await userEvent.selectOptions(screen.getByLabelText("Select diagram"), "2");
    expect(screen.getByTestId("diagram")).toHaveTextContent("classDiagram");
  });

  it("warns about invalid diagrams and partial generation failures", async () => {
    render(<MermaidPanel isProcessing={false} data={data} />);
    expect(screen.getByText(/Could not generate the architecture diagram/)).toBeInTheDocument();
    expect(screen.queryByText(/Unclosed brackets/)).not.toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Select diagram"), "2");
    expect(screen.getByText(/may contain syntax errors: Unclosed brackets/)).toBeInTheDocument();
  });

  it("falls back to the first diagram when a new run replaces the data", async () => {
    const { rerender } = render(<MermaidPanel isProcessing={false} data={data} />);
    await userEvent.selectOptions(screen.getByLabelText("Select diagram"), "2");

    const next = { ...data, diagrams: [{ ...data.diagrams[0], id: "9", mermaid_code: "erDiagram\nZ ||--o{ Y : q" }] };
    rerender(<MermaidPanel isProcessing={false} data={next} />);
    expect(screen.getByTestId("diagram")).toHaveTextContent("Z ||--o{ Y");
  });

  it("downloads the ZIP through the authenticated helper", async () => {
    downloadScaffold.mockResolvedValue(undefined);
    const scaffold = { document_id: "d", project_name: "Shop", directory_tree: "", file_count: 6, download_url: "/api/scaffold/d/download" };
    render(<MermaidPanel isProcessing={false} data={data} scaffoldData={scaffold} />);

    await userEvent.click(screen.getByRole("button", { name: /zip/i }));
    expect(downloadScaffold).toHaveBeenCalledWith("/api/scaffold/d/download", "Shop.zip");
  });

  it("shows a ZIP download failure instead of failing silently", async () => {
    downloadScaffold.mockImplementation(async () => {
      throw new Error("The ZIP is no longer available.");
    });
    const scaffold = { document_id: "d", project_name: "Shop", directory_tree: "", file_count: 6, download_url: "/x" };
    render(<MermaidPanel isProcessing={false} data={data} scaffoldData={scaffold} />);

    await userEvent.click(screen.getByRole("button", { name: /zip/i }));
    expect(await screen.findByText("The ZIP is no longer available.")).toBeInTheDocument();
  });
});
