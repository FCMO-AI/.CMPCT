/* Static gh-pages bootstrap for CMPCT Surface 0.29.g.
   Footnote: gh-pages is generated serving output only. The restored HTML shell is reused byte-for-byte
   from main, while this wrapper stamps the exact merged source/surface identity and activates the
   validated presentation layers before loading the unchanged Browser Lab controller. */
const replacements = new Map([
  ["__CMPCT_VERSION__", "0.29.0"],
  ["__FORMAT_REVISION__", "24"],
  ["__BUILD_COMMIT__", "f1d21a924d39"],
]);
const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
while (walker.nextNode()) {
  let value = walker.currentNode.nodeValue;
  for (const [from, to] of replacements) value = value.replaceAll(from, to);
  walker.currentNode.nodeValue = value;
}
const chip = document.querySelector(".release-chip");
if (chip) chip.textContent = "v0.29.0 · surface 0.29.g · r24";
const truth = document.querySelector(".truth-line");
if (truth) {
  const oldSurface = Array.from(truth.children).find((node) => node.textContent?.includes("Surface"));
  if (oldSurface) oldSurface.textContent = "Surface 0.29.g";
  else {
    const surface = document.createElement("span");
    surface.textContent = "Surface 0.29.g";
    truth.insertBefore(surface, truth.children[1] || null);
  }
}
for (const href of ["assets/motion.css", "assets/polish.css", "assets/experience.css"]) {
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}
import("./motion.js");
import("./experience.js");
import("./app-core.js");
