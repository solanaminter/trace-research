// Trace demo site — tiny enhancements only. No trackers, no external calls.
document.addEventListener("DOMContentLoaded", () => {
  // Add a "copy" affordance to terminal blocks on click (copies plain text).
  document.querySelectorAll("pre.term").forEach((block) => {
    block.title = "Click to copy";
    block.style.cursor = "copy";
    block.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(block.innerText);
        block.style.borderColor = "#76b900";
        setTimeout(() => (block.style.borderColor = ""), 600);
      } catch (e) {
        /* clipboard unavailable — harmless */
      }
    });
  });
});
