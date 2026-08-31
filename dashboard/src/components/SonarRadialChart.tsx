import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { ThreatStatItem } from "../lib/api/threats";

interface SonarRadialChartProps {
  data: ThreatStatItem[];
  selectedClass?: string | null;
  onSelectClass?: (threatClass: string) => void;
  width?: number;
  height?: number;
}

export const SonarRadialChart: React.FC<SonarRadialChartProps> = ({
  data,
  selectedClass,
  onSelectClass,
  width = 380,
  height = 380,
}) => {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!svgRef.current || !data || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const margin = 20;
    const radius = Math.min(width, height) / 2 - margin;
    const g = svg
      .append("g")
      .attr("transform", `translate(${width / 2},${height / 2})`);

    // Concentric Sonar Rings
    const rings = [0.25, 0.5, 0.75, 1.0];
    rings.forEach((rFactor) => {
      g.append("circle")
        .attr("r", radius * rFactor)
        .attr("fill", "none")
        .attr("stroke", "#3FC7D4")
        .attr("stroke-width", 1)
        .attr("stroke-opacity", rFactor === 1.0 ? 0.35 : 0.15)
        .attr("stroke-dasharray", rFactor === 1.0 ? "none" : "3,3");
    });

    // Crosshair axes
    g.append("line")
      .attr("x1", -radius)
      .attr("x2", radius)
      .attr("stroke", "#3FC7D4")
      .attr("stroke-opacity", 0.15);
    g.append("line")
      .attr("y1", -radius)
      .attr("y2", radius)
      .attr("stroke", "#3FC7D4")
      .attr("stroke-opacity", 0.15);

    // Color mapper
    const maxVal = d3.max(data, (d) => d.count) || 1000;
    const angleSlice = (Math.PI * 2) / data.length;

    // Sonar Wedge Segments
    data.forEach((d, i) => {
      const startAngle = i * angleSlice - Math.PI / 2;
      const endAngle = (i + 1) * angleSlice - Math.PI / 2;
      const wedgeRadius = (d.count / maxVal) * radius * 0.85 + radius * 0.15;
      const isSelected = selectedClass === d.threat_class;

      const arcGen = d3
        .arc()
        .innerRadius(15)
        .outerRadius(wedgeRadius)
        .startAngle(startAngle + 0.05)
        .endAngle(endAngle - 0.05);

      const color =
        d.avg_risk > 85
          ? "#FF4757"
          : d.avg_risk > 70
          ? "#FF8A3D"
          : "#3FC7D4";

      // Draw Arc
      g.append("path")
        .attr("d", arcGen as any)
        .attr("fill", color)
        .attr("fill-opacity", isSelected ? 0.85 : 0.45)
        .attr("stroke", color)
        .attr("stroke-width", isSelected ? 2 : 1)
        .style("cursor", "pointer")
        .on("click", () => onSelectClass && onSelectClass(d.threat_class))
        .append("title")
        .text(`${d.threat_class}: ${d.count} events (Risk: ${d.avg_risk})`);

      // Draw Peripheral Label
      const midAngle = (startAngle + endAngle) / 2;
      const labelRadius = radius * 0.96;
      const x = Math.cos(midAngle) * labelRadius;
      const y = Math.sin(midAngle) * labelRadius;

      g.append("text")
        .attr("x", x)
        .attr("y", y)
        .attr("text-anchor", x > 0 ? "start" : "end")
        .attr("dominant-baseline", "central")
        .attr("fill", isSelected ? "#3FC7D4" : "#8A95AA")
        .attr("font-family", "JetBrains Mono")
        .attr("font-size", "9px")
        .text(d.threat_class);
    });

    // Center Ping Core
    g.append("circle")
      .attr("r", 6)
      .attr("fill", "#3FC7D4")
      .attr("stroke", "#0B1220")
      .attr("stroke-width", 2);
  }, [data, selectedClass, width, height, onSelectClass]);

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="overflow-visible"
      />
    </div>
  );
};
