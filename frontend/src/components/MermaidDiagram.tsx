"use client";

import React, { useEffect, useRef, useImperativeHandle, forwardRef } from "react";
import mermaid from "mermaid";
import { useTheme } from "@/contexts/ThemeContext";

interface MermaidDiagramProps {
  chart: string;
}

export interface MermaidDiagramHandle {
  downloadPng: (filename?: string) => Promise<void>;
  getSvgElement: () => SVGSVGElement | null;
}

const MermaidDiagram = forwardRef<MermaidDiagramHandle, MermaidDiagramProps>(
  function MermaidDiagram({ chart }, ref) {
    const containerRef = useRef<HTMLDivElement>(null);
    const { theme } = useTheme();

    useEffect(() => {
      if (!containerRef.current || !chart) return;

      const render = async () => {
        try {
          mermaid.initialize({
            startOnLoad: false,
            theme: theme === "dark" ? "dark" : "default",
            securityLevel: "loose",
            fontFamily: "inherit",
          });

          // Generate a unique ID for this render
          const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2)}`;
          const { svg } = await mermaid.render(id, chart);

          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
            // Make SVG responsive
            const svgEl = containerRef.current.querySelector("svg");
            if (svgEl) {
              svgEl.style.maxWidth = "100%";
              svgEl.style.height = "auto";
            }
          }
        } catch (err) {
          console.error("Mermaid render error:", err);
          if (containerRef.current) {
            containerRef.current.innerHTML = `<pre style="color:var(--text-secondary);font-size:11px;padding:8px;white-space:pre-wrap">${chart}</pre>`;
          }
        }
      };

      render();
    }, [chart, theme]);

    // Expose download + SVG access to parent via ref
    useImperativeHandle(ref, () => ({
      getSvgElement: () =>
        containerRef.current?.querySelector("svg") ?? null,

      downloadPng: async (filename = "diagram.png") => {
        const svgEl = containerRef.current?.querySelector("svg");
        if (!svgEl) return;

        // Serialize SVG
        const serializer = new XMLSerializer();
        const svgStr = serializer.serializeToString(svgEl);
        const svgBlob = new Blob([svgStr], { type: "image/svg+xml;charset=utf-8" });
        const svgUrl = URL.createObjectURL(svgBlob);

        // Draw to canvas at 2× scale for retina quality
        const img = new Image();
        img.onload = () => {
          const scale = 2;
          const w = svgEl.viewBox.baseVal.width || svgEl.clientWidth || 1200;
          const h = svgEl.viewBox.baseVal.height || svgEl.clientHeight || 800;

          const canvas = document.createElement("canvas");
          canvas.width = w * scale;
          canvas.height = h * scale;

          const ctx = canvas.getContext("2d")!;
          // Fill background matching current theme
          ctx.fillStyle = theme === "dark" ? "#1e1e2e" : "#ffffff";
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.scale(scale, scale);
          ctx.drawImage(img, 0, 0);

          URL.revokeObjectURL(svgUrl);

          canvas.toBlob((blob) => {
            if (!blob) return;
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
          }, "image/png");
        };
        img.src = svgUrl;
      },
    }));

    return (
      <div
        ref={containerRef}
        className="w-full flex justify-center items-center"
        style={{ minHeight: "80px" }}
      />
    );
  }
);

MermaidDiagram.displayName = "MermaidDiagram";
export default MermaidDiagram;
