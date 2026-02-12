"use client"

import { useState } from "react"
import { MessageSquare, Trash2, Plus, ChevronLeft, ChevronRight, Pencil, Menu, X, PanelLeftClose, PanelLeftOpen } from "lucide-react"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"

interface Conversation {
    id: string
    title: string
    updated_at: string
}

interface SidebarProps {
    userId: string
    currentConversationId: string | null
    onSelectConversation: (id: string) => void
    onNewChat: () => void
    conversations: Conversation[]
    onDeleteConversation: (id: string) => void
    onRenameConversation: (id: string, newTitle: string) => void
    isLoading?: boolean
    isOpen: boolean
    onToggle: () => void
}

function groupConversationsByDate(conversations: Conversation[]) {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const sevenDaysAgo = new Date(today)
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

    const groups: { label: string; items: Conversation[] }[] = [
        { label: "Today", items: [] },
        { label: "Yesterday", items: [] },
        { label: "Previous 7 Days", items: [] },
        { label: "Previous 30 Days", items: [] },
        { label: "Older", items: [] },
    ]

    for (const conv of conversations) {
        const d = new Date(conv.updated_at)
        if (d >= today) groups[0].items.push(conv)
        else if (d >= yesterday) groups[1].items.push(conv)
        else if (d >= sevenDaysAgo) groups[2].items.push(conv)
        else if (d >= thirtyDaysAgo) groups[3].items.push(conv)
        else groups[4].items.push(conv)
    }

    return groups.filter(g => g.items.length > 0)
}

// Sekhmet Logo SVG component
export function SekhmetLogo({ className }: { className?: string }) {
    return (
        <div className={cn("w-7 h-7 bg-white rounded-lg flex items-center justify-center shadow-lg shadow-white/5", className)}>
            <div className="w-3.5 h-3.5 bg-black rounded-[2px]" />
        </div>
    )
}

// Conversation list content (shared between expanded desktop and mobile overlay)
function ConversationList({
    conversations,
    currentConversationId,
    onSelectConversation,
    onDeleteConversation,
    onRenameConversation,
    isLoading,
}: {
    conversations: Conversation[]
    currentConversationId: string | null
    onSelectConversation: (id: string) => void
    onDeleteConversation: (id: string) => void
    onRenameConversation: (id: string, newTitle: string) => void
    isLoading?: boolean
}) {
    const [editingId, setEditingId] = useState<string | null>(null)
    const [editTitle, setEditTitle] = useState("")
    const grouped = groupConversationsByDate(conversations)

    const startEditing = (e: React.MouseEvent, conv: Conversation) => {
        e.stopPropagation()
        setEditingId(conv.id)
        setEditTitle(conv.title)
    }

    const saveEditing = (id: string) => {
        if (editTitle.trim()) onRenameConversation(id, editTitle)
        setEditingId(null)
    }

    const handleKeyDown = (e: React.KeyboardEvent, id: string) => {
        if (e.key === 'Enter') saveEditing(id)
        else if (e.key === 'Escape') setEditingId(null)
    }

    if (isLoading) {
        return (
            <div className="px-3 py-6 text-center">
                <div className="flex flex-col items-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/10 border-t-white/40 rounded-full animate-spin" />
                    <span className="text-[11px] text-white/20">Loading history...</span>
                </div>
            </div>
        )
    }

    if (conversations.length === 0) {
        return (
            <div className="px-3 py-8 text-center">
                <p className="text-xs text-white/20">No conversations yet</p>
            </div>
        )
    }

    return (
        <>
            {grouped.map(group => (
                <div key={group.label} className="mb-4">
                    <h3 className="px-3 py-1.5 text-[11px] font-semibold text-white/30 uppercase tracking-wider">
                        {group.label}
                    </h3>
                    <div className="space-y-0.5">
                        {group.items.map(conv => {
                            const isActive = currentConversationId === conv.id
                            const isEditing = editingId === conv.id

                            return (
                                <div
                                    key={conv.id}
                                    className={cn(
                                        "group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all relative",
                                        isActive
                                            ? "bg-white/[0.08] text-white"
                                            : "text-white/60 hover:bg-white/[0.04] hover:text-white/80"
                                    )}
                                    onClick={() => onSelectConversation(conv.id)}
                                >
                                    {isEditing ? (
                                        <input
                                            autoFocus
                                            value={editTitle}
                                            onChange={(e) => setEditTitle(e.target.value)}
                                            onBlur={() => saveEditing(conv.id)}
                                            onKeyDown={(e) => handleKeyDown(e, conv.id)}
                                            onClick={(e) => e.stopPropagation()}
                                            className="flex-1 bg-transparent border-b border-blue-500/60 text-sm focus:outline-none text-white py-0 min-w-0"
                                        />
                                    ) : (
                                        <span className="flex-1 truncate text-[13px]">
                                            {conv.title || "Untitled"}
                                        </span>
                                    )}

                                    {!isEditing && (
                                        <div className={cn(
                                            "flex items-center gap-0.5 transition-opacity",
                                            isActive ? "opacity-60 hover:opacity-100" : "opacity-0 group-hover:opacity-60 group-hover:hover:opacity-100"
                                        )}>
                                            <button
                                                onClick={(e) => startEditing(e, conv)}
                                                className="p-1 rounded hover:bg-white/10 text-white/50 hover:text-white transition-all"
                                                title="Rename"
                                            >
                                                <Pencil className="w-3 h-3" />
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    onDeleteConversation(conv.id)
                                                }}
                                                className="p-1 rounded hover:bg-white/10 text-white/50 hover:text-red-400 transition-all"
                                                title="Delete"
                                            >
                                                <Trash2 className="w-3 h-3" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                </div>
            ))}
        </>
    )
}

export function Sidebar({
    userId,
    currentConversationId,
    onSelectConversation,
    onNewChat,
    conversations,
    onDeleteConversation,
    onRenameConversation,
    isLoading,
    isOpen,
    onToggle
}: SidebarProps) {

    return (
        <>
            {/* ===== DESKTOP SIDEBAR ===== */}
            {/* Collapsed icon rail — always visible on desktop */}
            {/* Collapsed icon rail — always visible on desktop */}
            <div className={cn(
                "hidden md:flex fixed top-0 left-0 h-full z-40 flex-col items-center bg-[#0a0a0a] border-r border-white/[0.06] transition-all duration-300 ease-in-out py-4 gap-4",
                isOpen ? "w-0 opacity-0 pointer-events-none overflow-hidden" : "w-[60px] opacity-100"
            )}>
                {/* Logo / Expand Toggle */}
                <button
                    onClick={onToggle}
                    className="relative group p-2 rounded-xl text-white/50 hover:text-white transition-all"
                    title="Expand sidebar"
                >
                    <div className="absolute inset-0 flex items-center justify-center transition-opacity duration-200 opacity-100 group-hover:opacity-0">
                        <SekhmetLogo />
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center transition-opacity duration-200 opacity-0 group-hover:opacity-100">
                        <PanelLeftOpen className="w-6 h-6" strokeWidth={1.5} />
                    </div>
                    <div className="w-7 h-7" /> {/* Spacer to maintain size */}
                </button>

                {/* New Chat */}
                <button
                    onClick={onNewChat}
                    className="mt-2 p-2 rounded-lg hover:bg-white/[0.08] text-white/50 hover:text-white transition-all"
                    title="New chat"
                >
                    <Plus className="w-6 h-6" strokeWidth={1.5} />
                </button>
            </div>

            {/* Expanded panel — desktop */}
            <div className={cn(
                "hidden md:flex fixed top-0 left-0 h-full z-40 flex-col bg-[#0a0a0a] border-r border-white/[0.06] transition-all duration-300 ease-in-out w-[260px]",
                isOpen ? "translate-x-0 opacity-100" : "-translate-x-full opacity-0 pointer-events-none"
            )}>
                {/* Header */}
                <div className="flex items-center gap-3 px-3 pt-4 pb-2">
                    <div className="flex items-center gap-2">
                        <SekhmetLogo />
                        <span className="text-sm font-semibold text-white/80 tracking-tight">Sekhmet</span>
                    </div>
                    <div className="flex-1" />
                    <button
                        onClick={onToggle}
                        className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] text-white/40 hover:text-white/80 transition-all border border-white/[0.02]"
                        title="Close sidebar"
                    >
                        <PanelLeftClose className="w-4 h-4" />
                    </button>
                </div>

                <div className="px-3 pb-2">
                    <button
                        onClick={onNewChat}
                        className="flex items-center gap-2 w-full px-3 py-2 rounded-lg hover:bg-white/[0.06] text-white/60 hover:text-white transition-all group"
                    >
                        <Plus className="w-4 h-4 group-hover:scale-110 transition-transform" />
                        <span className="text-sm font-medium">New chat</span>
                    </button>
                </div>

                {/* Conversation List */}
                <div className="flex-1 overflow-y-auto px-2 py-2 custom-scrollbar">
                    <ConversationList
                        conversations={conversations}
                        currentConversationId={currentConversationId}
                        onSelectConversation={onSelectConversation}
                        onDeleteConversation={onDeleteConversation}
                        onRenameConversation={onRenameConversation}
                        isLoading={isLoading}
                    />
                </div>

                {/* Footer */}
                <div className="px-3 py-3 border-t border-white/[0.06]">
                    <div className="flex items-center gap-3 px-2 py-2 rounded-lg">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-[10px] font-bold text-white shrink-0">
                            {userId !== "Guest" ? userId.charAt(0).toUpperCase() : "G"}
                        </div>
                        <div className="flex flex-col overflow-hidden">
                            <span className="text-xs font-medium text-white/70 truncate">
                                {userId !== "Guest" ? userId.slice(0, 12) : "Guest"}
                            </span>
                            <span className="text-[10px] text-white/30">Connected</span>
                        </div>
                    </div>
                </div>
            </div>


            {/* ===== MOBILE SIDEBAR ===== */}
            {/* Backdrop */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
                        onClick={onToggle}
                    />
                )}
            </AnimatePresence>

            {/* Mobile slide-over panel */}
            <div className={cn(
                "md:hidden fixed top-0 left-0 h-full z-50 flex flex-col bg-[#0a0a0a] border-r border-white/[0.06] transition-transform duration-300 ease-in-out w-[280px]",
                isOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                {/* Header */}
                <div className="flex items-center gap-2 px-3 pt-4 pb-2">
                    <SekhmetLogo />
                    <span className="text-sm font-semibold text-white/80 tracking-tight"></span>
                    <div className="flex-1" />
                    <button
                        onClick={onToggle}
                        className="p-2 rounded-lg hover:bg-white/[0.06] text-white/40 hover:text-white/70 transition-all"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* New Chat Button */}
                <div className="px-3 pb-2">
                    <button
                        onClick={() => { onNewChat(); onToggle(); }}
                        className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-white/[0.08] hover:bg-white/[0.04] text-white/70 hover:text-white transition-all text-sm"
                    >
                        <Plus className="w-4 h-4" />
                        New chat
                    </button>
                </div>

                {/* Conversation List */}
                <div className="flex-1 overflow-y-auto px-2 py-2 custom-scrollbar">
                    <ConversationList
                        conversations={conversations}
                        currentConversationId={currentConversationId}
                        onSelectConversation={(id) => { onSelectConversation(id); onToggle(); }}
                        onDeleteConversation={onDeleteConversation}
                        onRenameConversation={onRenameConversation}
                        isLoading={isLoading}
                    />
                </div>

                {/* Footer */}
                <div className="px-3 py-3 border-t border-white/[0.06]">
                    <div className="flex items-center gap-3 px-2 py-2 rounded-lg">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-[10px] font-bold text-white shrink-0">
                            {userId !== "Guest" ? userId.charAt(0).toUpperCase() : "G"}
                        </div>
                        <div className="flex flex-col overflow-hidden">
                            <span className="text-xs font-medium text-white/70 truncate">
                                {userId !== "Guest" ? userId.slice(0, 12) : "Guest"}
                            </span>
                            <span className="text-[10px] text-white/30">Connected</span>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}
