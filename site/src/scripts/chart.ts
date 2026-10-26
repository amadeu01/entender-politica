// Renders every `.plot[data-config]` on the page with Observable Plot.
// The static table view and provenance next to each chart carry the same data, so the
// chart enhances the page but never gates a value (see the figure's <details>).
import * as Plot from "@observablehq/plot";

type Point = {
  key: string;
  year: number;
  value: number;
  lower: number | null;
  upper: number | null;
  series_break: boolean;
};
type Config = {
  lang: "pt" | "en";
  log: boolean;
  unitLabel: string;
  decimals: number;
  keys: { key: string; label: string; slot: number }[];
  points: Point[];
  periods: { name: string; start: string; end: string | null }[];
  text: { year: string; seriesBreak: string };
};

const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function decimalYear(iso: string): number {
  const d = new Date(iso + "T00:00:00Z");
  const start = Date.UTC(d.getUTCFullYear(), 0, 1);
  const next = Date.UTC(d.getUTCFullYear() + 1, 0, 1);
  return d.getUTCFullYear() + (d.getTime() - start) / (next - start);
}

/** Insert explicit gaps so lines never bridge missing years (no interpolation). */
function withGaps(points: Point[]): (Point | { key: string; year: number; value: number })[] {
  const out: (Point | { key: string; year: number; value: number })[] = [];
  const byKey = Map.groupBy(points, (p) => p.key);
  for (const [key, list] of byKey) {
    list.sort((a, b) => a.year - b.year);
    list.forEach((p, i) => {
      if (i > 0 && p.year - list[i - 1].year > 1) out.push({ key, year: p.year - 0.5, value: NaN });
      out.push(p);
    });
  }
  return out;
}

function render(el: HTMLElement): void {
  const cfg: Config = JSON.parse(el.dataset.config!);
  const locale = cfg.lang === "pt" ? "pt-BR" : "en-US";
  const fmt = new Intl.NumberFormat(locale, {
    minimumFractionDigits: cfg.decimals,
    maximumFractionDigits: cfg.decimals,
  });
  const color = new Map(cfg.keys.map((k) => [k.key, css(`--series-${k.slot}`)]));
  const label = new Map(cfg.keys.map((k) => [k.key, k.label]));
  const points = cfg.log ? cfg.points.filter((p) => p.value > 0) : cfg.points;
  if (points.length === 0) return;

  const years = points.map((p) => p.year);
  const [x0, x1] = [Math.min(...years), Math.max(...years)];
  const width = el.clientWidth || 640;
  const narrow = width < 560;
  // One band per person in office: consecutive terms and acting periods are merged,
  // and bands alternate between shaded and clear.
  const blocks: { name: string; x1: number; x2: number }[] = [];
  for (const p of cfg.periods) {
    const x2 = p.end ? decimalYear(p.end) : x1 + 0.5;
    const last = blocks.at(-1);
    if (last?.name === p.name) last.x2 = x2;
    else blocks.push({ name: p.name, x1: decimalYear(p.start), x2 });
  }
  const bands = blocks
    .map((b, i) => ({ ...b, i, x1: Math.max(b.x1, x0 - 0.5), x2: Math.min(b.x2, x1 + 0.5) }))
    .filter((b) => b.x2 > b.x1);
  const shaded = bands.filter((b) => b.i % 2 === 0);
  const named = bands.filter((b) => b.x2 - b.x1 >= (narrow ? 4 : 2));

  const byYear = Map.groupBy(points, (p) => p.year);
  const tips = [...byYear].map(([year, list]) => ({
    year,
    text: [
      String(year),
      ...cfg.keys
        .map((k) => list.find((p) => p.key === k.key))
        .filter((p): p is Point => Boolean(p))
        .map(
          (p) =>
            `${fmt.format(p.value)}  ${label.get(p.key)}` +
            (p.series_break ? ` (${cfg.text.seriesBreak})` : ""),
        ),
    ].join("\n"),
  }));
  const ends = cfg.keys
    .map((k) => points.filter((p) => p.key === k.key).at(-1))
    .filter((p): p is Point => Boolean(p));
  const breaks = points.filter((p) => p.series_break);
  const has = new Set(points.map((p) => `${p.key}|${p.year}`));
  const isolated = points.filter(
    (p) => !has.has(`${p.key}|${p.year - 1}`) && !has.has(`${p.key}|${p.year + 1}`),
  );
  // Direct end labels only when few, short and with room; the legend is always present.
  const directLabels =
    cfg.keys.length > 1 && cfg.keys.length <= 4 && !narrow && cfg.keys.every((k) => k.label.length <= 16);

  const chart = Plot.plot({
    width,
    height: narrow ? 260 : 320,
    marginLeft: 52,
    marginRight: directLabels ? 110 : 16,
    marginTop: 22,
    style: { background: "transparent", color: css("--ink-2"), fontFamily: css("--font"), fontSize: "12px" },
    x: { domain: [x0 - 0.5, x1 + 0.5], tickFormat: (d: number) => String(d), label: null, ticks: narrow ? 5 : 10 },
    y: {
      type: cfg.log ? "log" : "linear",
      grid: true,
      label: cfg.unitLabel,
      tickFormat: (d: number) => new Intl.NumberFormat(locale, { notation: "compact" }).format(d),
    },
    marks: [
      Plot.rect(shaded, { x1: "x1", x2: "x2", fill: css("--band") }),
      Plot.text(named, {
        x: (b) => (b.x1 + b.x2) / 2,
        text: "name",
        frameAnchor: "top",
        dy: -14,
        fill: css("--muted"),
        fontSize: 10,
      }),
      Plot.areaY(
        points.filter((p) => p.lower !== null && p.upper !== null),
        { x: "year", y1: "lower", y2: "upper", z: "key", fill: (p: Point) => color.get(p.key), fillOpacity: 0.14 },
      ),
      Plot.lineY(withGaps(points), {
        x: "year",
        y: "value",
        z: "key",
        stroke: (p: Point) => color.get(p.key),
        strokeWidth: 2,
        strokeLinejoin: "round",
        strokeLinecap: "round",
      }),
      // Years with no neighbor on either side have no line segment: draw them as dots.
      Plot.dot(isolated, {
        x: "year",
        y: "value",
        r: 4,
        fill: (p: Point) => color.get(p.key),
        stroke: css("--surface"),
        strokeWidth: 2,
      }),
      Plot.dot(breaks, {
        x: "year",
        y: "value",
        r: 5,
        fill: css("--surface"),
        stroke: (p: Point) => color.get(p.key),
        strokeWidth: 2,
      }),
      Plot.dot(ends, {
        x: "year",
        y: "value",
        r: 4,
        fill: (p: Point) => color.get(p.key),
        stroke: css("--surface"),
        strokeWidth: 2,
      }),
      directLabels
        ? Plot.text(ends, {
            x: "year",
            y: "value",
            text: (p: Point) => label.get(p.key),
            textAnchor: "start",
            dx: 8,
            fill: css("--ink-2"),
          })
        : null,
      Plot.ruleX(tips, Plot.pointerX({ x: "year", stroke: css("--axis") })),
      Plot.tip(
        tips,
        Plot.pointerX({
          x: "year",
          title: "text",
          frameAnchor: "top-left",
          fill: css("--surface"),
          stroke: css("--border"),
          textPadding: 8,
        }),
      ),
    ],
  });
  chart.setAttribute("aria-hidden", "true");
  el.replaceChildren(chart);
}

export function renderAll(): void {
  const plots = [...document.querySelectorAll<HTMLElement>(".plot[data-config]")];
  const draw = () => plots.forEach(render);
  draw();
  let width = window.innerWidth;
  window.addEventListener("resize", () => {
    if (Math.abs(window.innerWidth - width) < 40) return;
    width = window.innerWidth;
    draw();
  });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
}
