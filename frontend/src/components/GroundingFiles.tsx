"use client"

import { useState } from "react"
import { Globe, ExternalLink, X, ChevronRight } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

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
    const [isOpen, setIsOpen] = useState(false)

    if (!metadata || !metadata.chunks || metadata.chunks.length === 0) return null

    return (
        <>
            <div className="w-full mt-2 mb-2">
                <button
                    onClick={() => setIsOpen(true)}
                    className="flex items-center gap-2 px-3 py-2 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.05] rounded-lg transition-all group w-fit"
                >
                    <div className="w-5 h-5 rounded-md bg-blue-500/10 flex items-center justify-center">
                        <Globe className="w-3 h-3 text-blue-400" />
                    </div>
                    <span className="text-xs font-medium text-white/70 group-hover:text-white/90">
                        {metadata.chunks.length} Google Search Sources
                    </span>
                    <ChevronRight className="w-3 h-3 text-white/30 group-hover:text-white/50 ml-1" />
                </button>
            </div>

            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
                            onClick={() => setIsOpen(false)}
                        />

                        {/* DESKTOP SIDE PANEL */}
                        <motion.div
                            initial={{ x: "100%" }}
                            animate={{ x: 0 }}
                            exit={{ x: "100%" }}
                            transition={{ type: "spring", damping: 25, stiffness: 200 }}
                            className="hidden md:flex fixed top-0 right-0 h-full w-[400px] z-50 bg-[#0a0a0a] border-l border-white/[0.08] shadow-2xl flex-col"
                        >
                            <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
                                <div className="flex items-center gap-2">
                                    <Globe className="w-4 h-4 text-blue-400" />
                                    <h3 className="font-semibold text-white/90 text-sm">Search Sources</h3>
                                </div>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/50 hover:text-white transition-all"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                                <div className="space-y-3">
                                    {metadata.chunks.map((chunk, i) => (
                                        <SourceCard key={i} chunk={chunk} index={i} />
                                    ))}
                                </div>
                            </div>
                        </motion.div>

                        {/* MOBILE BOTTOM SHEET */}
                        <motion.div
                            initial={{ y: "100%" }}
                            animate={{ y: 0 }}
                            exit={{ y: "100%" }}
                            transition={{ type: "spring", damping: 25, stiffness: 200 }}
                            className="md:hidden fixed bottom-0 left-0 w-full z-50 bg-[#121212] border-t border-white/[0.08] rounded-t-3xl shadow-2xl flex flex-col max-h-[80vh]"
                        >
                            <div className="flex flex-col items-center pt-3 pb-4 border-b border-white/[0.06]">
                                <div className="w-10 h-1 bg-white/20 rounded-full mb-4" />
                                <div className="flex items-center justify-between w-full px-5">
                                    <div className="flex items-center gap-2">
                                        <Globe className="w-4 h-4 text-blue-400" />
                                        <h3 className="font-semibold text-white/90 text-sm">Search Sources</h3>
                                    </div>
                                    <button
                                        onClick={() => setIsOpen(false)}
                                        className="p-1.5 rounded-full bg-white/[0.06] text-white/60"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                                <div className="space-y-3 pb-8">
                                    {metadata.chunks.map((chunk, i) => (
                                        <SourceCard key={i} chunk={chunk} index={i} />
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    )
}

function SourceCard({ chunk, index }: { chunk: any, index: number }) {
    return (
        <a
            href={chunk.url || "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-3 p-3 glass-card rounded-xl border border-white/[0.06] hover:bg-white/[0.04] transition-all group"
        >
            <div className="mt-0.5 min-w-[20px] h-5 flex items-center justify-center bg-white/[0.08] rounded-md text-[10px] text-white/50 font-mono font-medium">
                {index + 1}
            </div>
            <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-blue-300 leading-snug group-hover:text-blue-200 transition-colors line-clamp-2">
                    {chunk.title || "Untitled Source"}
                </h4>
                <div className="flex items-center gap-1.5 mt-1.5">
                    <div className="w-3 h-3 rounded-full bg-white/[0.06] flex items-center justify-center">
                        <img
                            src={`https://www.google.com/s2/favicons?domain=${new URL(chunk.url || "https://google.com").hostname}&sz=32`}
                            alt="fav"
                            className="w-2 h-2 opacity-60"
                            onError={(e) => (e.currentTarget.style.display = 'none')}
                        />
                    </div>
                    <span className="text-[11px] text-white/40 truncate max-w-[200px]">
                        {new URL(chunk.url || "https://google.com").hostname.replace('www.', '')}
                    </span>
                    <ExternalLink className="w-3 h-3 text-white/20 opacity-0 group-hover:opacity-100 transition-opacity ml-auto" />
                </div>
            </div>
        </a>
    )
}
