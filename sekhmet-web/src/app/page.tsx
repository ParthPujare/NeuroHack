"use client"

import { useState } from "react"
import Hero from "@/components/Hero"
import ChatInterface from "@/components/ChatInterface"
import { AnimatePresence, motion } from "framer-motion"

export default function Home() {
  const [view, setView] = useState<"landing" | "chat">("landing")

  return (
    <main className="min-h-screen bg-[#050505]">
      <AnimatePresence mode="wait">
        {view === "landing" ? (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
            transition={{ duration: 0.5 }}
          >
            <Hero onStart={() => setView("chat")} />
          </motion.div>
        ) : (
          <motion.div
            key="chat"
            initial={{ opacity: 0, scale: 1.02 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <ChatInterface onBack={() => setView("landing")} />
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  )
}
