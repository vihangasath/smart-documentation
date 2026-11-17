"use client";

import React, { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import mermaid from "mermaid";
import { useTheme } from "@/contexts/ThemeContext";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { ZoomIn, ZoomOut, ScanSearch } from "lucide-react";

interface MermaidDiagramProps {
  chart: string;
}

export interface MermaidDiagramHandle {
  downloadPng: (filename?: string) => Promise<void>;
  getSvgElement: () => SVGSVGElement | null;
}

const SCALE = 2; // retina-quality PNG

function svgSize(svg: SVGSVGElement): { width: number; height: number } {
  const vb = svg.viewBox?.baseVal;
  if (vb && vb.width > 0 && vb.height > 0) return { width: vb.width, height: vb.height };
  const box = svg.getBBox();
  return { width: box.width || 1200, height: box.height || 800 };
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Could not render the diagram as an image."));
    img.src = url;
  });
}

const MermaidDiagram = forwardRef<MermaidDiagramHandle, MermaidDiagramProps>(
  function MermaidDiagram({ chart }, ref) {
    const containerRef = useRef<HTMLDivElement>(null);
    const { theme } = useTheme();

    useEffect(() => {
      const container = containerRef.current;
      if (!container || !chart) return;
      let cancelled = false;

      // "strict" stops diagram code (which is AI output derived from user
      // documents) from running scripts or injecting HTML. Plain SVG labels keep
      // the diagram exportable to PNG in every browser.
      mermaid.initialize({
        startOnLoad: false,
        theme: theme === "dark" ? "dark" : "default",
        securityLevel: "strict",
        fontFamily: "inherit",
        htmlLabels: false,
        flowchart: { htmlLabels: false },
        class: { htmlLabels: false },
      });

      const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      mermaid
        .render(id, chart)
        .then(({ svg }) => {
          if (cancelled) return;
          container.innerHTML = svg;
          const svgEl = container.querySelector("svg");
          if (svgEl) {
            svgEl.style.maxWidth = "100%";
            svgEl.style.maxHeight = "100%";
            svgEl.style.height = "auto";
            svgEl.style.display = "block";
            svgEl.style.margin = "auto";
          }
        })
        .catch((err) => {
          console.error("Mermaid render error:", err);
          document.getElementById(`d${id}`)?.remove(); // mermaid leaves an error node behind
          if (cancelled) return;
          // Show the source as TEXT — never as HTML.
          const pre = document.createElement("pre");
          pre.style.cssText =
            "color:var(--text-secondary);font-size:11px;padding:8px;white-space:pre-wrap";
          pre.textContent = chart;
          container.replaceChildren(pre);
        });

      return () => {
        cancelled = true;
      };
    }, [chart, theme]);

    useImperativeHandle(ref, () => ({
      getSvgElement: () => containerRef.current?.querySelector("svg") ?? null,

      downloadPng: async (filename = "diagram.png") => {
        const svgEl = containerRef.current?.querySelector("svg");
        if (!svgEl) throw new Error("Nothing to export yet.");

        // Work on a clone so the live (zoomable) diagram is never touched.
        const { width, height } = svgSize(svgEl);
        const clone = svgEl.cloneNode(true) as SVGSVGElement;
        clone.removeAttribute("style");
        clone.setAttribute("width", String(width));
        clone.setAttribute("height", String(height));
        if (!clone.getAttribute("xmlns")) clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");

        const svgUrl = URL.createObjectURL(
          new Blob([new XMLSerializer().serializeToString(clone)], {
            type: "image/svg+xml;charset=utf-8",
          }),
        );
        try {
          const img = await loadImage(svgUrl);
          const canvas = document.createElement("canvas");
          canvas.width = width * SCALE;
          canvas.height = height * SCALE;
          const ctx = canvas.getContext("2d");
          if (!ctx) throw new Error("Canvas is not available in this browser.");
          ctx.fillStyle = theme === "dark" ? "#1e1e2e" : "#ffffff";
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.scale(SCALE, SCALE);
          ctx.drawImage(img, 0, 0, width, height);

          const blob = await new Promise<Blob>((resolve, reject) =>
            canvas.toBlob(
              (b) => (b ? resolve(b) : reject(new Error("Could not create the PNG."))),
              "image/png",
            ),
          );
          const pngUrl = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = pngUrl;
          link.download = filename;
          link.click();
          setTimeout(() => URL.revokeObjectURL(pngUrl), 1000);
        } finally {
          URL.revokeObjectURL(svgUrl);
        }
      },
    }));

    return (
      <div className="relative w-full h-full flex flex-col group">
        <TransformWrapper
          initialScale={1}
          minScale={0.1}
          maxScale={8}
          centerOnInit={true}
          wheel={{ step: 0.1 }}
          panning={{ velocityDisabled: true }}
        >
          {({ zoomIn, zoomOut, resetTransform }) => (
            <>
              {/* Zoom Controls overlay */}
              <div
                className="absolute bottom-4 right-4 z-10 flex gap-1.5 p-1.5 rounded-xl shadow-lg border opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity duration-200"
                style={{
                  background: "var(--bg-card)",
                  borderColor: "var(--border-color)",
                  backdropFilter: "blur(8px)",
                }}
              >
                <button
                  onClick={() => zoomIn(0.5)}
                  className="p-1.5 rounded-lg hover:bg-blue-500/10 hover:text-blue-500 transition-colors"
                  title="Zoom In"
                  aria-label="Zoom in"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
                <button
                  onClick={() => zoomOut(0.5)}
                  className="p-1.5 rounded-lg hover:bg-blue-500/10 hover:text-blue-500 transition-colors"
                  title="Zoom Out"
                  aria-label="Zoom out"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <div className="w-px h-5 my-auto mx-0.5" style={{ background: "var(--border-color)" }} />
                <button
                  onClick={() => resetTransform()}
                  className="p-1.5 rounded-lg hover:bg-blue-500/10 hover:text-blue-500 transition-colors"
                  title="Fit to Screen"
                  aria-label="Fit to screen"
                >
                  <ScanSearch className="w-4 h-4" />
                </button>
              </div>

              <TransformComponent
                wrapperStyle={{ width: "100%", height: "100%", cursor: "grab" }}
                contentStyle={{
                  width: "100%",
                  height: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <div ref={containerRef} className="w-full h-full flex justify-center items-center p-8" />
              </TransformComponent>
            </>
          )}
        </TransformWrapper>
      </div>
    );
  },
);

MermaidDiagram.displayName = "MermaidDiagram";
export default MermaidDiagram;
