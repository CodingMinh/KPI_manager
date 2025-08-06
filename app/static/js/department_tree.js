function toggleNode(span) {
  const nextUl = span.nextElementSibling;
  if (nextUl && nextUl.tagName === "UL") {
    nextUl.style.display = nextUl.style.display === "none" ? "block" : "none";
  }
}