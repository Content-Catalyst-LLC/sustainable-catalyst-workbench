/** UVR-01.3.3 — Static SVG export for numeric Graph Studio view series.
 * Only numeric points are accepted. No scientific validation is implied.
 * This is an export utility, not a report-attachment endpoint.
 */
import { verifyGraphReportPackage } from "./report-render-package.mjs";
const escapeXml = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&apos;"}[c]));
function pointsFromSeries(series) {
  const raw = series?.points;
  if (!Array.isArray(raw) || raw.length < 2) throw new TypeError("Series requires at least two explicit numeric points");
  return raw.map(p => {
    const x = Array.isArray(p) ? p[0] : p?.x;
    const y = Array.isArray(p) ? p[1] : p?.y;
    if (typeof x !== "number" || typeof y !== "number" || !Number.isFinite(x) || !Number.isFinite(y)) throw new TypeError("All points must be finite numeric x/y pairs");
    return {x,y};
  });
}
export function renderReportSvg(pkg,{width=900,height=550}={}) {
  if (!verifyGraphReportPackage(pkg)) throw new Error("Invalid or modified report package");
  if (!Number.isInteger(width)||width<240||width>4000||!Number.isInteger(height)||height<180||height>4000) throw new RangeError("Invalid SVG size");
  if (!Array.isArray(pkg.views)||!pkg.views.length) throw new TypeError("No views");
  const series = pkg.views.flatMap(v=>Array.isArray(v.series)?v.series:[]);
  if (!series.length) throw new TypeError("No render series");
  const datasets=series.map(pointsFromSeries);
  const all=datasets.flat();
  let minX=Math.min(...all.map(p=>p.x)),maxX=Math.max(...all.map(p=>p.x));
  let minY=Math.min(...all.map(p=>p.y)),maxY=Math.max(...all.map(p=>p.y));
  if (minX===maxX) {minX-=1;maxX+=1;} if(minY===maxY){minY-=1;maxY+=1;}
  const left=74,right=26,top=75,bottom=65,plotW=width-left-right,plotH=height-top-bottom;
  const X=x=>left+(x-minX)/(maxX-minX)*plotW;
  const Y=y=>top+(maxY-y)/(maxY-minY)*plotH;
  const palette=["#b42318","#007a3d","#314b74","#74532d","#755494"];
  const lines=datasets.map((d,i)=>`<polyline fill="none" stroke="${palette[i%palette.length]}" stroke-width="2.5" stroke-linejoin="round" points="${d.map(p=>`${X(p.x).toFixed(2)},${Y(p.y).toFixed(2)}`).join(" ")}"/>`).join("");
  const title=escapeXml(pkg.figureReference?.title||"Report figure");
  const caption=escapeXml(pkg.figureReference?.caption||"");
  const hash=escapeXml(pkg.artifactSha256);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="${title}"><title>${title}</title><desc>${caption}</desc><metadata>sc-workbench-report-view-spec/1.0 sha256:${hash}</metadata><rect width="100%" height="100%" fill="#ffffff"/><text x="${left}" y="40" font-family="sans-serif" font-size="20" fill="#111">${title}</text><path d="M ${left} ${top} V ${top+plotH} H ${left+plotW}" fill="none" stroke="#555" stroke-width="1.5"/>${lines}<text x="${left}" y="${height-22}" font-size="12" font-family="sans-serif" fill="#444">${escapeXml(minX.toPrecision(4))} to ${escapeXml(maxX.toPrecision(4))} (x)</text><text x="${width-right}" y="${height-22}" text-anchor="end" font-size="12" font-family="sans-serif" fill="#444">${escapeXml(minY.toPrecision(4))} to ${escapeXml(maxY.toPrecision(4))} (y)</text></svg>`;
}
