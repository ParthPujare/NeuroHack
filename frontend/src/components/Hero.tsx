"use client"

import { motion } from "framer-motion"
import { ArrowRight, Sparkles } from "lucide-react"

interface HeroProps {
    onStart: () => void
}

export default function Hero({ onStart }: HeroProps) {
    return (
        <div className="relative min-h-screen flex flex-col items-center justify-center px-4 overflow-hidden bg-[#050505]">
            {/* Background Glows */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-white/5 rounded-full blur-[120px] pointer-events-none" />

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="text-center z-20 max-w-4xl flex flex-col items-center"
            >

                <h1 className="text-7xl md:text-9xl font-bold tracking-tighter mb-8">
                    <span className="text-white drop-shadow-2xl">Sekhmet</span>
                </h1>

                <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-10 text-gradient leading-tight">
                    All your AI, Unified in One Intelligent Nest.
                </h2>

                <p className="text-lg md:text-xl text-white/50 mb-14 max-w-2xl mx-auto leading-relaxed px-4">
                    Orchestrate models, agents, and data with precision. Sekhmet is your modular
                    command center for everything AI — designed for clarity, speed, and control.
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mb-20">
                    <button
                        onClick={onStart}
                        className="group relative px-10 py-5 bg-white text-black font-bold rounded-2xl overflow-hidden transition-all hover:scale-105 active:scale-95 shadow-[0_0_30px_rgba(255,255,255,0.2)]"
                    >
                        <div className="flex items-center gap-2">
                            Start Free
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </button>
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1, duration: 1 }}
                className="absolute bottom-16 text-center z-20"
            >
                <p className="text-[10px] md:text-xs text-white/30 tracking-[0.3em] font-bold uppercase">
                    Trusted By AI Power Users Worldwide
                </p>
            </motion.div>

            {/* Decorative semi-circle */}
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[180%] md:w-[120%] aspect-square border-t-2 border-white/20 rounded-full translate-y-2/3 pointer-events-none shadow-[0_-50px_150px_rgba(255,255,255,0.1)] z-10" />
        </div>
    )
}
