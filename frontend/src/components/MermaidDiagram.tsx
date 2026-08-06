"use client";

import React, { useEffect, useRef, useImperativeHandle, forwardRef } from "react";
import mermaid from "mermaid";
import { useTheme } from "@/contexts/ThemeContext";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { ZoomIn, ZoomOut, Maximize, ScanSearch } from "lucide-react";

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

          const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2)}`;
          const { svg } = await mermaid.render(id, chart);

          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
            const svgEl = containerRef.current.querySelector("svg");
            if (svgEl) {
              // Ensure SVG fits nicely within the TransformComponent initially
              svgEl.style.maxWidth = "100%";
              svgEl.style.maxHeight = "100%";
              svgEl.style.height = "auto";
              svgEl.style.display = "block";
              svgEl.style.margin = "auto";
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

    useImperativeHandle(ref, () => ({
      getSvgElement: () => containerRef.current?.querySelector("svg") ?? null,

      downloadPng: async (filename = "diagram.png") => {
        const svgEl = containerRef.current?.querySelector("svg");
        if (!svgEl) return;

        // Temporarily remove CSS scaling constraints to get the true intrinsic SVG size for rendering
        const originalMaxWidth = svgEl.style.maxWidth;
        const originalMaxHeight = svgEl.style.maxHeight;
        const originalHeight = svgEl.style.height;
        const originalWidthAttr = svgEl.getAttribute("width");
        const originalHeightAttr = svgEl.getAttribute("height");

        svgEl.style.maxWidth = "none";
        svgEl.style.maxHeight = "none";
        svgEl.style.height = "none";
        
        let intrinsicWidth = svgEl.viewBox.baseVal.width || 1200;
        let intrinsicHeight = svgEl.viewBox.baseVal.height || 800;

        // Fallback to bounding box if viewBox is missing/zero
        if (intrinsicWidth === 0 || intrinsicHeight === 0) {
          const bbox = svgEl.getBBox();
          intrinsicWidth = bbox.width;
          intrinsicHeight = bbox.height;
        }

        svgEl.setAttribute("width", intrinsicWidth.toString());
        svgEl.setAttribute("height", intrinsicHeight.toString());

        const serializer = new XMLSerializer();
        const svgStr = serializer.serializeToString(svgEl);

        // Restore styles immediately
        svgEl.style.maxWidth = originalMaxWidth;
        svgEl.style.maxHeight = originalMaxHeight;
        svgEl.style.height = originalHeight;
        if (originalWidthAttr) svgEl.setAttribute("width", originalWidthAttr);
        else svgEl.removeAttribute("width");
        if (originalHeightAttr) svgEl.setAttribute("height", originalHeightAttr);
        else svgEl.removeAttribute("height");

        const svgBlob = new Blob([svgStr], { type: "image/svg+xml;charset=utf-8" });
        const svgUrl = URL.createObjectURL(svgBlob);

        const img = new Image();
        img.onload = () => {
          const scale = 2; // Retina resolution
          const canvas = document.createElement("canvas");
          canvas.width = intrinsicWidth * scale;
          canvas.height = intrinsicHeight * scale;

          const ctx = canvas.getContext("2d")!;
          ctx.fillStyle = theme === "dark" ? "#1e1e2e" : "#ffffff";
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.scale(scale, scale);
          ctx.drawImage(img, 0, 0, intrinsicWidth, intrinsicHeight);

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
                className="absolute bottom-4 right-4 z-10 flex gap-1.5 p-1.5 rounded-xl shadow-lg border opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                style={{ 
                  background: "var(--bg-card)", 
                  borderColor: "var(--border-color)",
                  backdropFilter: "blur(8px)"
                }}
              >
                <button
                  onClick={() => zoomIn(0.5)}
                  className="p-1.5 rounded-lg hover:bg-blue-500/10 hover:text-blue-500 transition-colors"
                  title="Zoom In"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
                <button
                  onClick={() => zoomOut(0.5)}
                  className="p-1.5 rounded-lg hover:bg-blue-500/10 hover:text-blue-500 transition-colors"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <div className="w-px h-5 my-auto mx-0.5" style={{ background: "var(--border-color)" }} />
                <button
                  onClick={() => resetTransform()}
                  className="p-1.5 rounded-lg hover:bg-blue-500/10 hover:text-blue-500 transition-colors"
                  title="Fit to Screen"
                >
                  <ScanSearch className="w-4 h-4" />
                </button>
              </div>

              <TransformComponent 
                wrapperStyle={{ width: "100%", height: "100%", cursor: "grab" }}
                contentStyle={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}
              >
                <div ref={containerRef} className="w-full h-full flex justify-center items-center p-8" />
              </TransformComponent>
            </>
          )}
        </TransformWrapper>
      </div>
    );
  }
);

MermaidDiagram.displayName = "MermaidDiagram";
export default MermaidDiagram;
