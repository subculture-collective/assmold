import { readFile, writeFile } from 'node:fs/promises';

const root = new URL('../dist/', import.meta.url);
const source = await readFile(new URL('index.html', root), 'utf8');
const origin = 'https://assmold.subcult.tv';
const pages = [
  [
    '',
    'assmold — Unofficial broadcast archive',
    'Search statements from Asmongold broadcasts with timestamps and original video context. An independent archive built by SUBCULT.',
  ],
  [
    'about',
    'About the archive — assmold',
    'How this independent archive keeps searchable transcripts, timestamps and links to the original recordings.',
  ],
  [
    'support',
    'Support SUBCULT — assmold',
    'Support SUBCULT, the studio maintaining the archive tools. Contributions go to the studio, not Asmongold, and do not buy editorial influence.',
  ],
];
const escape = (value) =>
  value
    .replaceAll('&', '&amp;')
    .replaceAll('"', '&quot;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
// Deep dynamic routes retain a neutral shell, rather than canonicalizing to home.
await writeFile(new URL('app.html', root), source);
for (const [path, title, description] of pages) {
  let page = source
    .replace(/<title>.*?<\/title>/s, `<title>${escape(title)}</title>`)
    .replace(
      /<meta\s+name="description"[^>]*>/s,
      `<meta name="description" content="${escape(description)}">`
    );
  const url = origin + '/' + path;
  const metadata = `<link rel="canonical" href="${url}">\n<meta property="og:type" content="website">\n<meta property="og:title" content="${escape(title)}">\n<meta property="og:description" content="${escape(description)}">\n<meta property="og:url" content="${url}">\n`;
  page = page.replace('</head>', metadata + '</head>');
  await writeFile(new URL(path ? path + '.html' : 'index.html', root), page);
}
await writeFile(
  new URL('robots.txt', root),
  `User-agent: *\nAllow: /\n\nSitemap: ${origin}/sitemap.xml\n`
);
await writeFile(
  new URL('sitemap.xml', root),
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    pages.map(([path]) => `<url><loc>${origin}/${path}</loc></url>`).join('') +
    '</urlset>\n'
);
