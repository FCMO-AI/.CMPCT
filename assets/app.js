/* Static gh-pages bootstrap for CMPCT.
   Footnote: gh-pages contains generated public artifacts only. Canonical source remains on main; this
   wrapper stamps source metadata and presentation-only layers before loading the unchanged Browser Lab
   controller. It deliberately does not alter benchmark numbers or archive semantics. */
const replacements = new Map([
  ["__CMPCT_VERSION__", "0.29.0"],
  ["__FORMAT_REVISION__", "24"],
  ["__BUILD_COMMIT__", "f6bbdee3380e"],
]);
const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
while (walker.nextNode()) {
  let value = walker.currentNode.nodeValue;
  for (const [from, to] of replacements) value = value.replaceAll(from, to);
  walker.currentNode.nodeValue = value;
}
const chip = document.querySelector(".release-chip");
if (chip) chip.textContent = "v0.29.0 · surface 0.29.c · r24";
const truth = document.querySelector(".truth-line");
if (truth && !Array.from(truth.children).some((node) => node.textContent?.includes("Surface"))) {
  const surface = document.createElement("span");
  surface.textContent = "Surface 0.29.c";
  truth.insertBefore(surface, truth.children[1] || null);
}
for (const href of ["assets/motion.css", "assets/polish.css"]) {
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}
import("./motion.js");
import("./app-core.js");
