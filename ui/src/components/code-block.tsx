import { useState, useEffect } from 'react';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import rehypeStringify from 'rehype-stringify';
import rehypePrettyCode from 'rehype-pretty-code';
import { transformerCopyButton } from '@rehype-pretty/transformers';

async function highlightCode(code: string, language?: string) {
  const file = await unified()
    .use(remarkParse)
    .use(remarkRehype)
    .use(rehypePrettyCode, {
      theme: 'github-light',
      keepBackground: false,
      transformers: [
        transformerCopyButton({
          visibility: 'always',
          feedbackDuration: 3_000,
        }),
      ],
    })
    .use(rehypeStringify)
    .process('```' + (language || '') + '\n' + code.trimStart() + '\n```');

  return String(file);
}

export function CodeBlock({
  code,
  language,
  className,
}: {
  code: string;
  language?: string;
  className?: string;
}) {
  const [highlightedCode, setHighlightedCode] = useState<string | null>(null);

  useEffect(() => {
    highlightCode(code, language).then(setHighlightedCode);
  }, [code, language]);

  return (
    <section
      className={className || ''}
      dangerouslySetInnerHTML={{
        __html: highlightedCode || '',
      }}
    />
  );
}
