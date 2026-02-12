"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
    Clock,
    Map,
    Database,
    Scale,
    PenTool,
    MessageSquare,
    ChevronDown,
    ChevronRight,
    Activity,
    Search,
    BrainCircuit
} from "lucide-react"
import { cn } from "@/lib/utils"

interface ThinkingProcessProps {
    details: any
}

export function ThinkingProcess({ details }: ThinkingProcessProps) {
    const [isOpen, setIsOpen] = useState(false)
    const [activeTab, setActiveTab] = useState<string>("temporal")

    if (!details) return null

    const steps = [
        { id: "temporal", label: "Temporal", icon: Clock },
        { id: "planner", label: "Planner", icon: Map },
        { id: "retrieval", label: "Retrieval", icon: Database },
        { id: "reconciliation", label: "Reconcile", icon: Scale },
        { id: "synthesis", label: "Synthesis", icon: PenTool },
        { id: "response", label: "Final Prompt", icon: MessageSquare },
    ]

    const getStepContent = (stepId: string) => {
        const data = details[`step${steps.findIndex(s => s.id === stepId)}_` + (stepId === "response" ? "response" : stepId === "temporal" ? "temporal_check" : stepId)]

        if (!data) return <div className="text-white/30 italic">No data available for this step.</div>

        switch (stepId) {
            case "temporal":
                return (
                    <div className="space-y-4">
                        <div className="flex gap-4">
                            <div className="glass p-3 rounded-xl flex-1 border-white/5">
                                <span className="text-xs text-white/40 block mb-1">Override Detected</span>
                                <span className={cn("text-sm font-medium", data.is_override ? "text-amber-400" : "text-emerald-400")}>
                                    {data.is_override ? "Yes" : "No"}
                                </span>
                            </div>
                            <div className="glass p-3 rounded-xl flex-1 border-white/5">
                                <span className="text-xs text-white/40 block mb-1">Model</span>
                                <span className="text-sm font-medium text-white/80">{data.model || "Unknown"}</span>
                            </div>
                        </div>
                        {data.conflict_summary && (
                            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                                <span className="text-xs text-amber-400 block mb-1">Conflict Summary</span>
                                <p className="text-sm text-amber-200/80">{data.conflict_summary}</p>
                            </div>
                        )}
                        {data.target_node_label && !data.conflict_summary && (
                            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                                <span className="text-xs text-blue-400 block mb-1">Targeting</span>
                                <p className="text-sm text-blue-200/80 w-full break-words">{data.target_node_label}</p>
                            </div>
                        )}
                        {data.prompt && (
                            <div className="mt-4">
                                <span className="text-xs text-white/40 block mb-2">System Prompt</span>
                                <pre className="p-3 bg-black/30 rounded-xl text-[10px] text-white/50 overflow-x-auto border border-white/5 font-mono whitespace-pre-wrap">
                                    {data.prompt}
                                </pre>
                            </div>
                        )}
                    </div>
                )

            case "planner":
                return (
                    <div className="space-y-4">
                        {data.search_terms && (
                            <div>
                                <span className="text-xs text-white/40 block mb-2">Vector Search Terms</span>
                                <div className="flex flex-wrap gap-2">
                                    {data.search_terms.map((term: string, i: number) => (
                                        <span key={i} className="px-2 py-1 bg-white/5 rounded-lg text-xs text-blue-300 border border-white/5">
                                            {term}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                        {data.cypher_query && (
                            <div>
                                <span className="text-xs text-white/40 block mb-2">Graph Query</span>
                                <pre className="p-3 bg-black/30 rounded-xl text-[10px] text-emerald-300 overflow-x-auto border border-white/5 font-mono">
                                    {data.cypher_query}
                                </pre>
                            </div>
                        )}
                        {data.prompt && (
                            <div className="mt-4">
                                <span className="text-xs text-white/40 block mb-2">System Prompt</span>
                                <pre className="p-3 bg-black/30 rounded-xl text-[10px] text-white/50 overflow-x-auto border border-white/5 font-mono whitespace-pre-wrap">
                                    {data.prompt}
                                </pre>
                            </div>
                        )}
                    </div>
                )

            case "retrieval":
                return (
                    <div className="space-y-6">
                        {/* Vector Results */}
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <Search className="w-3 h-3 text-purple-400" />
                                <span className="text-xs font-semibold text-white/60">Vector Context</span>
                            </div>
                            {data.vector && data.vector.length > 0 ? (
                                <div className="space-y-2">
                                    {data.vector.map((v: any, i: number) => (
                                        <div key={i} className="p-3 glass rounded-xl border-white/5 text-xs text-white/70">
                                            {typeof v === 'string' ? v : v.content || JSON.stringify(v)}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-xs text-white/30 italic px-2">No vector memories found.</div>
                            )}
                        </div>

                        {/* Graph Results */}
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <BrainCircuit className="w-3 h-3 text-emerald-400" />
                                <span className="text-xs font-semibold text-white/60">Graph Context</span>
                            </div>
                            {data.graph && data.graph.length > 0 ? (
                                <div className="space-y-2">
                                    {data.graph.map((g: any, i: number) => (
                                        <div key={i} className="p-3 glass rounded-xl border-white/5 text-xs text-white/70 font-mono">
                                            {JSON.stringify(g, null, 2)}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-xs text-white/30 italic px-2">No graph connections found.</div>
                            )}
                        </div>
                    </div>
                )

            case "reconciliation":
                return (
                    <div>
                        <span className="text-xs text-white/40 block mb-2">Technique: {data.model || "Rule Based"}</span>
                        <div className="p-4 glass rounded-xl border-white/5 text-xs text-white/70 leading-relaxed whitespace-pre-wrap font-mono">
                            {typeof data === 'string' ? data : data.content || JSON.stringify(data, null, 2)}
                        </div>
                    </div>
                )

            case "synthesis":
                return (
                    <div>
                        <div className="p-4 glass rounded-xl border-white/5 text-sm text-white/80 leading-relaxed whitespace-pre-wrap">
                            {data.content || JSON.stringify(data)}
                        </div>
                    </div>
                )

            case "response":
                return (
                    <div>
                        <span className="text-xs text-white/40 block mb-2">Final System Prompt</span>
                        <pre className="p-4 bg-black/30 rounded-xl text-[10px] text-white/60 overflow-x-auto border border-white/5 font-mono whitespace-pre-wrap">
                            {data.prompt || "No prompt available"}
                        </pre>
                    </div>
                )

            default:
                return null
        }
    }

    return (
        <div className="w-full max-w-[95%]">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="group flex items-center gap-3 px-1 py-2 w-full text-left"
            >
                <div className={cn(
                    "w-6 h-6 rounded-lg flex items-center justify-center transition-colors",
                    isOpen ? "bg-blue-500/20 text-blue-400" : "bg-white/5 text-white/40 group-hover:text-white/70"
                )}>
                    <Activity className="w-3.5 h-3.5" />
                </div>
                <span className="text-xs font-bold tracking-wider uppercase text-white/40 group-hover:text-white/70 transition-colors">
                    Neural Processing
                </span>
                <div className={cn(
                    "ml-auto transition-transform duration-300 text-white/20",
                    isOpen ? "rotate-90" : "rotate-0"
                )}>
                    <ChevronRight className="w-4 h-4" />
                </div>
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="pt-2 pb-6">
                            <div className="bg-[#0A0A0A] border border-white/10 rounded-2xl overflow-hidden flex flex-col md:flex-row">
                                {/* Tabs */}
                                <div className="flex md:flex-col border-b md:border-b-0 md:border-r border-white/5 bg-white/[0.02]">
                                    {steps.map((step) => {
                                        const StepIcon = step.icon
                                        const isActive = activeTab === step.id
                                        const hasData = details[`step${steps.findIndex(s => s.id === step.id)}_` + (step.id === "response" ? "response" : step.id === "temporal" ? "temporal_check" : step.id)]

                                        if (!hasData) return null

                                        return (
                                            <button
                                                key={step.id}
                                                onClick={() => setActiveTab(step.id)}
                                                className={cn(
                                                    "flex items-center gap-3 px-4 py-3 md:py-4 md:px-6 hover:bg-white/5 transition-all text-left relative",
                                                    isActive ? "text-blue-400 bg-white/5" : "text-white/40"
                                                )}
                                            >
                                                <StepIcon className="w-4 h-4" />
                                                <span className="hidden md:block text-xs font-semibold uppercase tracking-wider">
                                                    {step.label}
                                                </span>
                                                {isActive && (
                                                    <div className="absolute bottom-0 md:bottom-auto md:right-0 left-0 md:left-auto md:top-0 w-full md:w-[2px] h-[2px] md:h-full bg-blue-500" />
                                                )}
                                            </button>
                                        )
                                    })}
                                </div>

                                {/* Content */}
                                <div className="flex-1 p-6 bg-black/20 min-h-[300px]">
                                    <AnimatePresence mode="wait">
                                        <motion.div
                                            key={activeTab}
                                            initial={{ opacity: 0, x: 10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: -10 }}
                                            transition={{ duration: 0.2 }}
                                        >
                                            {getStepContent(activeTab)}
                                        </motion.div>
                                    </AnimatePresence>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
