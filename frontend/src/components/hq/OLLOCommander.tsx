import { useEffect, useRef, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useTranslation } from "react-i18next"
import { queryOLLO } from "../../api/ollo"
import { useNavigate } from "react-router-dom"
import type { OLLOResponse, OLLOBriefing } from "../../types/ollo"

interface Props {
  greeting: OLLOResponse | null
  briefing: OLLOBriefing | null
  loading: boolean
  error: string | null
}

type DisplayMode = "conversation" | "briefing"

interface ChatMessage {
  role: "user" | "assistant"
  text: string
  intent_route?: string | null
}

const SpeechRecognition =
  (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

export default function OLLOCommander({ greeting, briefing, loading, error }: Props) {
  const { t } = useTranslation("commandDeck")
  const [mode, setMode] = useState<DisplayMode>("conversation")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState("")
  const [isQuerying, setIsQuerying] = useState(false)

  // Voice States
  const [lang, setLang] = useState<"en-US" | "tr-TR">(() => {
    const isTr = navigator.language?.toLowerCase().startsWith("tr")
    return isTr ? "tr-TR" : "en-US"
  })
  const [isListening, setIsListening] = useState(false)
  const [speechError, setSpeechError] = useState<string | null>(null)
  const [ttsEnabled, setTtsEnabled] = useState(true)

  const recognitionRef = useRef<any>(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (briefing && !greeting) setMode("briefing")
  }, [briefing, greeting])

  // Initialize Speech Recognition
  useEffect(() => {
    if (SpeechRecognition) {
      const rec = new SpeechRecognition()
      rec.continuous = false
      rec.interimResults = false
      rec.maxAlternatives = 1

      rec.onstart = () => {
        setIsListening(true)
        setSpeechError(null)
      }

      rec.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript
        if (transcript) {
          setInputText(transcript)
          handleSend(transcript)
        }
      }

      rec.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error)
        setSpeechError(t("olloCommander.errors.voiceError", { error: event.error }))
        setIsListening(false)
      }

      rec.onend = () => {
        setIsListening(false)
      }

      recognitionRef.current = rec
    }
  }, [lang])

  const toggleListening = () => {
    if (!SpeechRecognition) {
      setSpeechError(t("olloCommander.errors.speechNotSupported"))
      return
    }
    if (isListening) {
      recognitionRef.current?.stop()
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.lang = lang
        try {
          recognitionRef.current.start()
        } catch (e) {
          console.error(e)
        }
      }
    }
  }

  const speakResponse = (text: string) => {
    if (!ttsEnabled || !window.speechSynthesis) return
    window.speechSynthesis.cancel()

    const cleanText = text.replace(/[#*`_]/g, "").trim()
    const utterance = new SpeechSynthesisUtterance(cleanText)
    utterance.lang = lang

    const voices = window.speechSynthesis.getVoices()
    const matchingVoice = voices.find((v) => v.lang.startsWith(lang.split("-")[0]))
    if (matchingVoice) {
      utterance.voice = matchingVoice
    }

    window.speechSynthesis.speak(utterance)
  }

  const handleSend = async (queryText?: string) => {
    const textToSubmit = queryText || inputText
    if (!textToSubmit.trim()) return

    setMode("conversation")
    const userMsg: ChatMessage = { role: "user", text: textToSubmit }
    setMessages((prev) => [...prev, userMsg])
    setInputText("")
    setIsQuerying(true)
    setSpeechError(null)

    try {
      const response = await queryOLLO(textToSubmit)
      const assistMsg: ChatMessage = {
        role: "assistant",
        text: response.text,
        intent_route: response.intent_route,
      }
      setMessages((prev) => [...prev, assistMsg])

      speakResponse(response.text)

      if (response.intent_route) {
        setTimeout(() => {
          navigate(response.intent_route!)
        }, 1200)
      }
    } catch (e: any) {
      console.error(e)
      setSpeechError(t("olloCommander.errors.fetchFailed"))
    } finally {
      setIsQuerying(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div
          className="rounded-full"
          style={{
            width: 80,
            height: 80,
            background: "radial-gradient(circle at 35% 35%, rgba(79,140,255,0.1), rgba(79,140,255,0.02), transparent)",
            border: "1px solid rgba(79,140,255,0.06)",
            animation: "ollo-breathe 3s ease-in-out infinite",
          }}
        />
        <div className="h-1.5 skeleton-pulse w-24 mt-5" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div
          className="rounded-full flex items-center justify-center"
          style={{
            width: 64,
            height: 64,
            border: "1px solid rgba(255, 93, 115, 0.15)",
            background: "rgba(255, 93, 115, 0.03)",
          }}
        >
          <span className="text-lg" style={{ color: "rgba(255, 93, 115, 0.4)" }}>◉</span>
        </div>
        <p className="mt-3 text-[10px] font-mono" style={{ color: "rgba(255, 93, 115, 0.6)" }}>{error}</p>
      </div>
    )
  }

  const displayBriefing = mode === "briefing" && briefing

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-lg mt-4 px-2">

      {/* Control Console */}
      <div className="flex items-center gap-3 mb-4 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-full px-4 py-1.5 shadow-sm">
        <button
          onClick={() => setLang((l) => (l === "en-US" ? "tr-TR" : "en-US"))}
          className="text-[10px] font-mono uppercase font-semibold text-[var(--accent-blue)] hover:text-[var(--accent-blue)]/80 transition-all"
          title="Change voice language (speech-to-text/text-to-speech) / Sesli dili değiştir"
        >
          {lang === "en-US" ? "English 🇺🇸" : "Türkçe 🇹🇷"}
        </button>

        <span className="w-px h-3 bg-[var(--border-subtle)]" />

        <button
          onClick={() => {
            setTtsEnabled(!ttsEnabled)
            if (ttsEnabled) window.speechSynthesis?.cancel()
          }}
          className="text-[10px] font-mono uppercase font-semibold transition-all"
          style={{ color: ttsEnabled ? "#3EDC97" : "var(--text-muted)" }}
        >
          {t("olloCommander.tts")}: {ttsEnabled ? t("olloCommander.on") : t("olloCommander.off")}
        </button>
      </div>

      {/* Primary Message Area */}
      <div className="w-full min-h-[140px] max-h-[300px] overflow-y-auto mb-4 p-4 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] backdrop-blur-md">
        <AnimatePresence mode="wait">
          {displayBriefing ? (
            <motion.div
              key="briefing"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="text-center"
            >
              <div
                className="text-[7px] font-medium uppercase tracking-[0.18em] mb-1"
                style={{ color: "var(--accent-blue)" }}
              >
                {briefing!.kind} {t("olloCommander.briefingSuffix")}
              </div>
              <h3 className="text-xs font-semibold leading-snug" style={{ color: "var(--text-primary)" }}>
                {briefing!.title}
              </h3>
              <p className="text-[10px] mt-2 leading-relaxed text-left" style={{ color: "var(--text-secondary)" }}>
                {briefing!.text}
              </p>
              <div className="mt-3 text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                {briefing!.provider} · {briefing!.model}
              </div>
            </motion.div>
          ) : greeting && messages.length === 0 ? (
            <motion.div
              key="greeting"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="text-center"
            >
              <h3 className="text-xs font-semibold leading-snug" style={{ color: "var(--text-primary)" }}>
                {greeting.text.split("\n")[0] || t("olloCommander.welcomeFallback")}
              </h3>
              {greeting.sections && greeting.sections.length > 0 ? (
                <div className="space-y-2 text-left mt-3">
                  {greeting.sections.map((section, idx) => (
                    <div key={idx}>
                      <div className="text-[7px] font-semibold uppercase tracking-[0.12em] mb-0.5" style={{ color: "var(--accent-blue)" }}>
                        {section.heading}
                      </div>
                      <p className="text-[10px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                        {section.content}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (() => {
                // The headline above is already greeting.text's first line
                // -- for a single-line greeting (e.g. the backend's raw
                // fallback error text, which has no newline at all) that
                // headline IS the full text, so rendering greeting.text
                // again here duplicated it verbatim underneath itself.
                // Only show a body paragraph when there's real content
                // beyond that first line.
                const remainder = greeting.text.split("\n").slice(1).join("\n").trim();
                return remainder ? (
                  <p className="text-[10px] mt-2 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                    {remainder}
                  </p>
                ) : null;
              })()}
              <div className="mt-3 text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                {greeting.provider} · {greeting.model} · {(greeting.duration_ms / 1000).toFixed(1)}s
              </div>
            </motion.div>
          ) : messages.length > 0 ? (
            <motion.div
              key="conversation"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-3"
            >
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[90%] rounded-xl px-3 py-1.5 ${
                      msg.role === "user"
                        ? "bg-[var(--accent-blue)]/15 border border-[var(--accent-blue)]/20 text-[var(--text-primary)]"
                        : "bg-transparent text-[var(--text-secondary)]"
                    }`}
                  >
                    <p className="text-[10px] leading-relaxed whitespace-pre-wrap font-sans">
                      {msg.text}
                    </p>
                    {msg.intent_route && (
                      <div className="text-[8px] font-mono text-[var(--accent-blue)] mt-1 animate-pulse">
                        {t("olloCommander.navigatingTo", { route: msg.intent_route })}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isQuerying && (
                <div className="flex justify-start">
                  <div className="flex gap-1 items-center px-3 py-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] animate-bounce" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] animate-bounce [animation-delay:0.15s]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] animate-bounce [animation-delay:0.3s]" />
                  </div>
                </div>
              )}
            </motion.div>
          ) : (
            <div className="text-center text-[10px] text-[var(--text-muted)] py-4">
              {t("olloCommander.awaitingConnection")}
            </div>
          )}
        </AnimatePresence>
      </div>

      {/* Input controls & Voice Microphone Trigger */}
      <div className="w-full flex gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend()
          }}
          placeholder={isListening ? t("olloCommander.placeholderListening") : t("olloCommander.placeholderInstruct")}
          disabled={isListening}
          className="flex-1 bg-[var(--bg-base)] rounded-xl px-4 py-2.5 text-[10px] font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-blue)] disabled:opacity-50"
        />

        <button
          onClick={toggleListening}
          className={`px-3.5 rounded-xl border flex items-center justify-center transition-all ${
            isListening
              ? "bg-[var(--accent-red)]/25 border-[var(--accent-red)]/50 text-[var(--accent-red)] animate-pulse"
              : "bg-[var(--bg-base)] border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          }`}
          title={isListening ? t("olloCommander.micStop") : t("olloCommander.micStart")}
        >
          <span className="text-sm">🎙️</span>
        </button>

        <button
          onClick={() => handleSend()}
          disabled={!inputText.trim() || isQuerying}
          className="px-4 rounded-xl bg-[var(--accent-blue)] text-white text-[10px] font-mono font-semibold hover:bg-[var(--accent-blue)]/90 disabled:opacity-40 transition-all shrink-0"
        >
          {t("olloCommander.send")}
        </button>
      </div>

      {speechError && (
        <div className="text-[9px] font-mono text-[var(--accent-red)] mt-2 bg-[var(--accent-red)]/10 px-3 py-1 rounded-md border border-[var(--accent-red)]/20">
          {speechError}
        </div>
      )}
    </div>
  )
}
