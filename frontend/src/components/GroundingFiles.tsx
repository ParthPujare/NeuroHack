"use client"

import { Globe, ExternalLink } from "lucide-react"

interface GroundingFilesProps {
    metadata: {
        chunks?: Array<{
            title?: string
            url?: string
            [key: string]: any
        }>
        [key: string]: any
    } | null
}

export function GroundingFiles({ metadata }: GroundingFilesProps) {
    if (!metadata || !metadata.chunks || metadata.chunks.length === 0) return null

    return (
        <div className="w-full mt-4 mb-2">
            <div className="flex items-center gap-2 mb-3 px-1">
                <Globe className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-xs font-bold tracking-wider uppercase text-white/40">
                    Trusted Knowledge Sources
                </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {metadata.chunks.map((chunk, i) => (
                    <a
                        key={i}
                        href={chunk.url || "#"}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-start gap-3 p-3 glass rounded-xl border-white/5 hover:bg-white/5 transition-all group"
                    >
                        <div className="mt-0.5 min-w-[16px] h-4 flex items-center justify-center bg-white/10 rounded text-[10px] text-white/50 font-mono">
                            {i + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                            <h4 className="text-xs font-medium text-blue-300 truncate group-hover:text-blue-200 transition-colors">
                                {chunk.title || "Untitled Source"}
                            </h4>
                            <div className="flex items-center gap-1 mt-1">
                                <span className="text-[10px] text-white/30 truncate max-w-[200px]">
                                    {chunk.url}
                                </span>
                                <ExternalLink className="w-2.5 h-2.5 text-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                        </div>
                    </a>
                ))}
            </div>
        </div>
    )
}
