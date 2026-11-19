"use client";

import { useState } from "react";
import type { SourceRef } from "../lib/chatStream";
import { ExternalIcon } from "./ui";

/** Only plain https photo addresses ever reach the page (the server enforces this too). */
const secure = (url?: string | null) => (url && /^https:\/\/[^\s"'<>]+$/.test(url) ? url : null);

export default function SourceCard({ source }: { source: SourceRef }) {
  const [broken, setBroken] = useState(false);
  const image = secure(source.image);

  return (
    <article className="card">
      {image && !broken && (
        // eslint-disable-next-line @next/next/no-img-element -- photos live on the source site's own CDN; this is a static export with no image optimiser
        <img
          src={image}
          alt={source.title}
          loading="lazy"
          width={400}
          height={160}
          referrerPolicy="no-referrer"
          onError={() => setBroken(true)}
        />
      )}
      <div className="card-body">
        <strong className="card-title">
          <span>[{source.n}]</span> {source.title}
        </strong>
        {source.detail && <p className="card-detail">{source.detail}</p>}
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Click to know more about ${source.title}`}
          className="btn btn-accent btn-sm"
        >
          Click to know more
          <ExternalIcon />
        </a>
      </div>
    </article>
  );
}
