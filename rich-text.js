const TOKEN_RE = /(\*\*__[\s\S]+?__\*\*|__\*\*[\s\S]+?\*\*__|\*\*[\s\S]+?\*\*|__[\s\S]+?__|\*[^*\n]+?\*)/g;

export function parseRichTextTokens(text) {
  const input = String(text ?? '');
  if (!input) return [];
  const tokens = [];
  let lastIndex = 0;

  for (const match of input.matchAll(TOKEN_RE)) {
    const idx = match.index ?? 0;
    if (idx > lastIndex) {
      tokens.push({ text: input.slice(lastIndex, idx), bold: false, italic: false, underline: false });
    }
    const raw = match[0];
    if ((raw.startsWith('**__') && raw.endsWith('__**')) || (raw.startsWith('__**') && raw.endsWith('**__'))) {
      tokens.push({ text: raw.slice(4, -4), bold: true, italic: false, underline: true });
    } else if (raw.startsWith('**') && raw.endsWith('**')) {
      tokens.push({ text: raw.slice(2, -2), bold: true, italic: false, underline: false });
    } else if (raw.startsWith('__') && raw.endsWith('__')) {
      tokens.push({ text: raw.slice(2, -2), bold: false, italic: false, underline: true });
    } else if (raw.startsWith('*') && raw.endsWith('*')) {
      tokens.push({ text: raw.slice(1, -1), bold: false, italic: true, underline: false });
    }
    lastIndex = idx + raw.length;
  }

  if (lastIndex < input.length) {
    tokens.push({ text: input.slice(lastIndex), bold: false, italic: false, underline: false });
  }
  return tokens;
}

export function stripRichTextMarkers(text) {
  return parseRichTextTokens(text).map((t) => t.text).join('');
}

export function renderRichText(element, text) {
  if (!element) return;
  const doc = element.ownerDocument || (typeof document !== 'undefined' ? document : null);
  if (!doc) {
    element.textContent = stripRichTextMarkers(text);
    return;
  }

  const tokens = parseRichTextTokens(text);
  const fragment = doc.createDocumentFragment();

  for (const token of tokens) {
    let node = doc.createTextNode(token.text);
    if (token.underline) {
      const u = doc.createElement('u');
      u.appendChild(node);
      node = u;
    }
    if (token.italic) {
      const em = doc.createElement('em');
      em.appendChild(node);
      node = em;
    }
    if (token.bold) {
      const strong = doc.createElement('strong');
      strong.appendChild(node);
      node = strong;
    }
    fragment.appendChild(node);
  }

  element.replaceChildren(fragment);
}
