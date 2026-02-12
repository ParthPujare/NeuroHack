"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Paperclip, X, Home, Loader2, ArrowUp } from "lucide-react"
import { cn } from "@/lib/utils"
// import { Sidebar } from "./Sidebar" // Assuming standard export, but code used named export
import { Sidebar } from "@/components/Sidebar"
import { getConversations, getMessages, createConversation, deleteConversation, updateConversationTitle } from "@/lib/api"

import { ThinkingProcess } from "./ThinkingProcess"
import { GroundingFiles } from "./GroundingFiles"

interface Message {
    role: "user" | "assistant"
    content: string
    files?: number
    details?: any
    grounding_metadata?: any
}

interface Conversation {
    id: string
    title: string
    updated_at: string
}

export default function ChatInterface({ onBack }: { onBack: () => void }) {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [attachedFiles, setAttachedFiles] = useState<File[]>([])
    const [userId, setUserId] = useState<string>("Guest")
    const [sidebarOpen, setSidebarOpen] = useState(true)

    // History State
    const [conversations, setConversations] = useState<Conversation[]>([])
    const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
    const [isHistoryLoading, setIsHistoryLoading] = useState(false)

    const fileInputRef = useRef<HTMLInputElement>(null)
    const scrollRef = useRef<HTMLDivElement>(null)

    // 1. Fetch User
    useEffect(() => {
        const fetchUser = async () => {
            try {
                const res = await fetch("http://localhost:8000/user")
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

    // 2. Fetch History when User is known
    useEffect(() => {
        if (userId === "Guest") return;

        const loadHistory = async () => {
            setIsHistoryLoading(true)
            try {
                const data = await getConversations(userId)
                setConversations(data)
            } catch (e) {
                console.error("Failed to load history:", e)
            } finally {
                setIsHistoryLoading(false)
            }
        }
        loadHistory()
    }, [userId])

    // Poll for title updates
    useEffect(() => {
        if (!currentConversationId || !userId) return;

        const currentConv = conversations.find(c => c.id === currentConversationId);
        if (currentConv?.title === "New Chat") {
            const interval = setInterval(async () => {
                try {
                    // Refresh just this conversation's title? Or all...
                    // Efficient way: fetch all history for now
                    const updatedConvs = await getConversations(userId);
                    setConversations(updatedConvs);

                    const updated = updatedConvs.find((c: any) => c.id === currentConversationId);
                    if (updated && updated.title !== "New Chat") {
                        clearInterval(interval);
                    }
                } catch (e) {
                    console.error("Polling error:", e);
                }
            }, 3000); // Check every 3s

            // Stop polling after 30s to save resources
            const timeout = setTimeout(() => clearInterval(interval), 30000);

            return () => {
                clearInterval(interval);
                clearTimeout(timeout);
            }
        }
    }, [currentConversationId, conversations, userId])


    // Scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [messages])

    // Handlers
    const handleNewChat = () => {
        setCurrentConversationId(null)
        setMessages([])
    }

    const handleSelectConversation = async (id: string) => {
        if (id === currentConversationId) return;

        setCurrentConversationId(id)
        setIsLoading(true)
        try {
            const data = await getMessages(id)
            setMessages(data.map((m: any) => ({
                role: m.role,
                content: m.content,
                details: m.metadata?.step_logs,
                grounding_metadata: m.metadata?.grounding_metadata
            })))
        } catch (e) {
            console.error("Failed to load messages:", e)
        } finally {
            setIsLoading(false)
        }
    }

    const handleDeleteConversation = async (id: string) => {
        try {
            await deleteConversation(id)
            setConversations(prev => prev.filter(c => c.id !== id))
            if (currentConversationId === id) {
                handleNewChat()
            }
        } catch (e) {
            console.error("Failed to delete conversation:", e)
        }
    }

    const handleRenameConversation = async (id: string, newTitle: string) => {
        try {
            await updateConversationTitle(id, newTitle)
            setConversations(prev => prev.map(c =>
                c.id === id ? { ...c, title: newTitle } : c
            ))
        } catch (e) {
            console.error("Failed to rename conversation:", e)
        }
    }

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
            // Ensure conversation exists
            let activeConvId = currentConversationId;
            if (!activeConvId) {
                try {
                    const newConv = await createConversation(userId, "New Chat")
                    activeConvId = newConv.id;
                    setCurrentConversationId(activeConvId)
                    setConversations(prev => [newConv, ...prev])
                } catch (e) {
                    console.error("Failed to create conversation:", e)
                }
            }

            const attachments = await Promise.all(attachedFiles.map(async f => ({
                name: f.name,
                mime_type: f.type,
                data: await toBase64(f)
            })))

            setAttachedFiles([])

            const response = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userMessage.content,
                    user_id: userId,
                    conversation_id: activeConvId,
                    attachments: attachments.length > 0 ? attachments : undefined
                })
            })

            if (response.ok) {
                const data = await response.json()
                setMessages(prev => [...prev, {
                    role: "assistant",
                    content: data.response,
                    details: data.step_logs,
                    grounding_metadata: data.grounding_metadata
                }])

                if (activeConvId) {
                    // Quietly refresh history to update titles/timestamps
                    getConversations(userId).then(setConversations).catch(console.error)
                }
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
            <Sidebar
                userId={userId}
                currentConversationId={currentConversationId}
                onSelectConversation={handleSelectConversation}
                onNewChat={handleNewChat}
                conversations={conversations}
                onDeleteConversation={handleDeleteConversation}
                onRenameConversation={handleRenameConversation}
                isLoading={isHistoryLoading}
                isOpen={sidebarOpen}
                onToggle={() => setSidebarOpen(prev => !prev)}
            />

            {/* Main Chat Area */}
            <div className={cn(
                "flex-1 flex flex-col relative min-w-0 bg-[#050505] transition-all duration-300",
                sidebarOpen ? "md:ml-[260px]" : "md:ml-0"
            )}>
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
                                    "flex flex-col gap-2 min-w-0",
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

                                {m.role === "assistant" && (
                                    <div className="w-full max-w-[90%] md:max-w-[80%] space-y-2">
                                        {m.grounding_metadata && <GroundingFiles metadata={m.grounding_metadata} />}
                                        {m.details && <ThinkingProcess details={m.details} />}
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
                <div className="absolute bottom-6 left-0 right-0 px-4 md:px-8 z-50">
                    <div className="max-w-2xl mx-auto flex flex-col gap-3">
                        {/* File Previews */}
                        <AnimatePresence>
                            {attachedFiles.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                    className="flex flex-wrap gap-2 p-3 rounded-2xl bg-white/[0.03] border border-white/[0.08]"
                                >
                                    {attachedFiles.map((file, i) => (
                                        <div key={i} className="flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-lg bg-white/5 border border-white/[0.06] group hover:bg-white/[0.08] transition-colors">
                                            <Paperclip className="w-3 h-3 text-white/40" />
                                            <span className="text-xs text-white/60 truncate max-w-[150px]">{file.name}</span>
                                            <button
                                                onClick={() => setAttachedFiles(prev => prev.filter((_, idx) => idx !== i))}
                                                className="p-0.5 rounded hover:bg-white/10 text-white/20 hover:text-red-400 transition-all"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </div>
                                    ))}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Input Container */}
                        <div className="relative">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                placeholder={isLoading ? "Processing..." : "Message Sekhmet..."}
                                className="w-full px-5 py-4 pr-24 bg-[#1a1a1a] border border-white/[0.08] rounded-2xl text-white text-[15px] placeholder:text-white/20 outline-none focus:border-white/20 transition-all"
                            />
                            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="p-2 rounded-lg hover:bg-white/[0.06] text-white/25 hover:text-white/60 transition-all"
                                    title="Attach file"
                                >
                                    <Paperclip className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={handleSend}
                                    disabled={!input.trim() && attachedFiles.length === 0}
                                    className={cn(
                                        "p-2 rounded-lg transition-all",
                                        input.trim() || attachedFiles.length > 0
                                            ? "bg-white text-black hover:bg-white/90 active:scale-95"
                                            : "bg-white/[0.06] text-white/20 cursor-not-allowed"
                                    )}
                                >
                                    {isLoading ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <ArrowUp className="w-4 h-4" />
                                    )}
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
