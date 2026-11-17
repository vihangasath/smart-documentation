import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import InputPanel from "./InputPanel";

const uploadDocument = vi.fn();
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, uploadDocument: (f: File) => uploadDocument(f) };
});

const file = (name: string) => new File(["x".repeat(80)], name, { type: "text/plain" });
const input = () => document.getElementById("srs-file-input") as HTMLInputElement;

beforeEach(() => {
  uploadDocument.mockReset();
});

describe("InputPanel", () => {
  it("shows the attached-file card for every type (including .md) and reports the id", async () => {
    uploadDocument.mockResolvedValue({ document_id: "d1", filename: "notes.md" });
    const onUploaded = vi.fn();
    render(<InputPanel value="" onChange={() => {}} onDocumentUploaded={onUploaded} />);

    await userEvent.upload(input(), file("notes.md"));

    expect(await screen.findByText("notes.md")).toBeInTheDocument();
    expect(onUploaded).toHaveBeenLastCalledWith("d1", "notes.md");
  });

  it("does not copy the file into the textarea (it is for instructions)", async () => {
    uploadDocument.mockResolvedValue({ document_id: "d1", filename: "a.txt" });
    const onChange = vi.fn();
    render(<InputPanel value="" onChange={onChange} />);
    await userEvent.upload(input(), file("a.txt"));
    await screen.findByText("a.txt");
    expect(onChange).not.toHaveBeenCalled();
  });

  it("shows upload errors below the dropzone and does not report a document", async () => {
    uploadDocument.mockImplementation(async () => {
      throw new Error("File exceeds 10MB limit.");
    });
    const onUploaded = vi.fn();
    render(<InputPanel value="" onChange={() => {}} onDocumentUploaded={onUploaded} />);

    await userEvent.upload(input(), file("big.txt"));

    expect(await screen.findByRole("alert")).toHaveTextContent("File exceeds 10MB limit.");
    expect(onUploaded).not.toHaveBeenCalledWith("d1", expect.anything());
  });

  it("no longer offers legacy .doc files", () => {
    render(<InputPanel value="" onChange={() => {}} />);
    expect(input().accept.split(",")).not.toContain(".doc");
    expect(input().accept).not.toMatch(/msword/);
  });

  it("removes the file when the user clicks remove", async () => {
    uploadDocument.mockResolvedValue({ document_id: "d1", filename: "a.txt" });
    const onUploaded = vi.fn();
    render(<InputPanel value="" onChange={() => {}} onDocumentUploaded={onUploaded} />);
    await userEvent.upload(input(), file("a.txt"));
    await userEvent.click(await screen.findByTitle("Remove file"));
    await waitFor(() => expect(onUploaded).toHaveBeenLastCalledWith("", ""));
  });
});
