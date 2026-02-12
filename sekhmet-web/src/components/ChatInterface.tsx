"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Plus, Paperclip, X, Trash2, Home, Search, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface Message {
    role: "user" | "assistant"
    content: string
    files?: number
    details?: any
}

export default function ChatInterface({ onBack }: { onBack: () => void }) {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [attachedFiles, setAttachedFiles] = useState<File[]>([])
    const [userId, setUserId] = useState<string>("Guest")
    const fileInputRef = useRef<HTMLInputElement>(null)
    const scrollRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        // Fetch User ID from Backend
        const fetchUser = async () => {
            try {
                // Pointing to Port 8001 where the FastAPI backend is now running with CORS enabled
                const res = await fetch("http://localhost:8001/user")
                if (res.ok) {
                    const data = await res.json()
                    setUserId(data.user_id)
                }
            } catch (e) {
                console.error("Failed to fetch user:", e)
            }
        }
        fetchUser()
    }, [])

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [messages])

    const handleSend = async () => {
        if (!input.trim() && attachedFiles.length === 0) return

        const userMessage: Message = {
            role: "user",
            content: input,
            files: attachedFiles.length > 0 ? attachedFiles.length : undefined
        }

        setMessages(prev => [...prev, userMessage])
        setInput("")
        setIsLoading(true)

        // Helper to convert file to base64
        const toBase64 = (file: File) => new Promise<string>((resolve, reject) => {
            const reader = new FileReader()
            reader.readAsDataURL(file)
            reader.onload = () => resolve((reader.result as string).split(',')[1])
            reader.onerror = error => reject(error)
        })

        try {
            const attachments = await Promise.all(attachedFiles.map(async f => ({
                name: f.name,
                mime_type: f.type,
                data: await toBase64(f)
            })))

            setAttachedFiles([])

            const response = await fetch("http://localhost:8001/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: input,
                    user_id: userId,
                    attachments: attachments.length > 0 ? attachments : undefined
                })
            })

            if (response.ok) {
                const data = await response.json()
                setMessages(prev => [...prev, {
                    role: "assistant",
                    content: data.response,
                    details: data.step_logs
                }])
            }
        } catch (error) {
            console.error("Chat error:", error)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="flex h-screen w-full bg-[#050505] overflow-hidden">
            {/* Sidebar */}
            <div className="w-80 glass-dark border-r border-white/5 p-8 flex flex-col gap-8 hidden md:flex shrink-0">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-lg shadow-white/5">
                        <div className="w-5 h-5 bg-black rounded-sm" />
                    </div>
                    <div className="flex flex-col">
                        <span className="text-2xl font-bold tracking-tighter text-white">Sekhmet</span>
                        <span className="text-[10px] text-white/40 font-bold uppercase tracking-[0.2em] leading-none mt-1">Matrix: {userId}</span>
                    </div>
                </div>

                <div className="flex flex-col gap-3 mt-10">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-white/30 font-black mb-2">Cognitive Layer</div>
                    <button onClick={onBack} className="flex items-center gap-4 px-5 py-3 rounded-xl hover:bg-white/5 text-white/50 hover:text-white transition-all group">
                        <Home className="w-5 h-5 group-hover:scale-110 transition-transform" />
                        <span className="font-semibold">Exit to Terminal</span>
                    </button>
                    <button onClick={() => setMessages([])} className="flex items-center gap-4 px-5 py-3 rounded-xl hover:bg-white/5 text-white/50 hover:text-white transition-all group">
                        <Trash2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
                        <span className="font-semibold">Purge Matrix</span>
                    </button>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative min-w-0 bg-[#050505]">
                {/* Header for Mobile */}
                <div className="md:hidden p-4 glass-dark border-b border-white/5 flex items-center justify-between">
                    <span className="font-bold text-white">Sekhmet</span>
                    <button onClick={onBack} className="p-2 glass rounded-lg"><Home className="w-4 h-4" /></button>
                </div>

                {/* Messages Container */}
                <div
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto px-4 md:px-8 pt-10 pb-40 flex flex-col items-center custom-scrollbar"
                >
                    <div className="w-full max-w-3xl space-y-10">
                        {messages.length === 0 && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="h-[70vh] flex flex-col items-center justify-center text-center px-6"
                            >
                                <div className="w-20 h-20 glass rounded-3xl flex items-center justify-center mb-8 rotate-12 glow-shadow">
                                    <div className="w-8 h-8 bg-white/10 rounded-lg animate-pulse" />
                                </div>
                                <h3 className="text-3xl font-bold text-white mb-4 tracking-tight">Awaiting Neural Pulse...</h3>
                                <p className="text-white/30 max-w-sm leading-relaxed text-sm">
                                    Injected knowledge modules or command the neural graph to begin cognitive orchestration.
                                </p>
                            </motion.div>
                        )}

                        {messages.map((m, i) => (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.98 }}
                                animate={{ opacity: 1, scale: 1 }}
                                key={i}
                                className={cn(
                                    "flex flex-col gap-4 min-w-0",
                                    m.role === "user" ? "items-end" : "items-start"
                                )}
                            >
                                <div className={cn(
                                    "p-5 rounded-2xl max-w-[90%] md:max-w-[80%] text-[15px] leading-relaxed break-words shadow-2xl",
                                    m.role === "user"
                                        ? "bg-white text-black font-semibold rounded-tr-none"
                                        : "glass border-white/10 text-white/90 rounded-tl-none backdrop-blur-3xl"
                                )}>
                                    {m.content}
                                </div>
                                {m.files && (
                                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full glass border-white/5 text-[10px] text-white/40 font-bold tracking-wider uppercase">
                                        <Paperclip className="w-3 h-3" />
                                        {m.files} Knowledge Modules Ingested
                                    </div>
                                )}
                                {m.details && (
                                    <div className="w-full max-w-[95%]">
                                        <details className="group">
                                            <summary className="text-[10px] uppercase tracking-[0.2em] text-white/20 cursor-pointer hover:text-white/40 transition-all px-1 flex items-center gap-2 font-bold py-2">
                                                <div className="w-1.5 h-1.5 rounded-full bg-blue-500/50 group-open:bg-blue-400 animate-pulse" />
                                                Epistemic Intelligence Logs
                                            </summary>
                                            <div className="mt-4 p-5 glass rounded-2xl text-xs overflow-x-auto text-white/50 font-mono border border-white/5 leading-relaxed bg-white/[0.01]">
                                                {JSON.stringify(m.details, null, 2)}
                                            </div>
                                        </details>
                                    </div>
                                )}
                            </motion.div>
                        ))}

                        {isLoading && (
                            <div className="flex flex-col gap-4 items-start">
                                <div className="p-5 glass rounded-2xl rounded-tl-none flex items-center gap-4 border-white/5 shadow-2xl">
                                    <div className="flex gap-1.5 px-2">
                                        <div className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <div className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <div className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                    <span className="text-[10px] uppercase tracking-[0.3em] font-black text-white/30">Orchestrating...</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Input Area - Floating Bar */}
                <div className="absolute bottom-10 left-0 right-0 px-4 md:px-10 z-50">
                    <div className="max-w-4xl mx-auto flex flex-col gap-6">
                        {/* File Previews */}
                        <AnimatePresence>
                            {attachedFiles.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                    className="flex flex-wrap gap-2 p-3 glass rounded-2xl border-white/10 shadow-2xl backdrop-blur-3xl"
                                >
                                    {attachedFiles.map((file, i) => (
                                        <div key={i} className="flex items-center gap-3 pl-3 pr-2 py-2 glass-dark rounded-xl border border-white/5 group bg-white/5 hover:bg-white/10 transition-colors">
                                            <Paperclip className="w-3.5 h-3.5 text-white/40" />
                                            <span className="text-xs text-white/70 truncate max-w-[150px] font-medium">{file.name}</span>
                                            <button
                                                onClick={() => setAttachedFiles(prev => prev.filter((_, idx) => idx !== i))}
                                                className="p-1 px-1.5 rounded-lg hover:bg-white/10 text-white/20 hover:text-red-400 transition-all"
                                            >
                                                <X className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    ))}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Input Container */}
                        <div className="relative group glow-shadow">
                            <div className="absolute inset-0 bg-white/5 rounded-3xl blur-2xl group-focus-within:bg-white/10 transition-all -z-10" />
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                placeholder="Sync with Sekhmet Matrix..."
                                className="w-full px-8 py-6 pr-40 glass-dark border border-white/20 rounded-[28px] text-white text-lg placeholder:text-white/10 outline-none focus:border-white/40 transition-all shadow-2xl backdrop-blur-3xl"
                            />
                            <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-3">
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="p-3.5 rounded-2xl hover:bg-white/5 text-white/20 hover:text-white transition-all active:scale-90"
                                    title="Attach Knowledge"
                                >
                                    <Paperclip className="w-6 h-6" />
                                </button>
                                <button
                                    onClick={handleSend}
                                    disabled={isLoading}
                                    className="p-4 bg-white text-black rounded-2xl hover:scale-110 active:scale-90 transition-all shadow-[0_0_40px_rgba(255,255,255,0.2)] disabled:opacity-50 disabled:scale-100 group"
                                >
                                    <Send className="w-6 h-6 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                                </button>
                            </div>
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="hidden"
                                multiple
                                onChange={(e) => setAttachedFiles(Array.from(e.target.files || []))}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
