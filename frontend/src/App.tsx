import { lazy, Suspense } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { ArrowDown, ArrowRight, FileText, History, MessageSquare, Search, ShieldCheck, Sparkles } from 'lucide-react'
import Navbar from './components/navigation/Navbar'

const KnowledgeOrbit = lazy(() => import('./components/visuals/KnowledgeOrbit'))

const features = [
  { icon: FileText, eyebrow: '01 / INGEST', title: 'Your documents, understood', description: 'Bring PDFs, text files and Word documents into one searchable knowledge space.', accent: 'cyan' },
  { icon: MessageSquare, eyebrow: '02 / EXPLORE', title: 'Conversations with context', description: 'Ask natural questions and keep the thread of your thinking across conversations.', accent: 'magenta' },
  { icon: Search, eyebrow: '03 / VERIFY', title: 'Answers grounded in sources', description: 'Get responses informed by relevant passages, not unsupported guesswork.', accent: 'cyan' },
  { icon: History, eyebrow: '04 / RETURN', title: 'Pick up where you left off', description: 'Your conversation history keeps important discoveries within reach.', accent: 'magenta' },
]

const steps = [
  { number: '01', title: 'Add your sources', description: 'Upload the documents you are studying, researching or working with.' },
  { number: '02', title: 'Build your knowledge space', description: 'AtlasGPT indexes the content so relevant information can be retrieved.' },
  { number: '03', title: 'Ask better questions', description: 'Explore ideas and get answers grounded in your own material.' },
]

function App() {
  const reduceMotion = useReducedMotion()
  const rise = reduceMotion ? {} : { initial: { opacity: 0, y: 22 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, amount: 0.18 }, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] as const } }

  return (
    <main className="min-h-screen overflow-hidden bg-atlas-pearl pt-[76px] text-atlas-navy">
      <Navbar />

      <section className="hero-grid relative mx-auto grid min-h-[calc(100svh-76px)] max-w-7xl items-center gap-8 px-6 py-16 sm:py-20 lg:grid-cols-[1.02fr_.98fr] lg:px-12">
        <div className="hero-copy relative z-10">
          <motion.div {...(reduceMotion ? {} : { initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.5 } })} className="mb-7 inline-flex items-center gap-2.5 rounded-full border border-atlas-mist bg-white/80 px-4 py-2 text-xs font-semibold tracking-wide text-atlas-deep-cyan shadow-sm shadow-atlas-navy/5">
            <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-atlas-cyan opacity-30" /><span className="relative inline-flex h-2 w-2 rounded-full bg-atlas-cyan" /></span>
            A clearer way to work with what you know
          </motion.div>
          <motion.h1 {...(reduceMotion ? {} : { initial: { opacity: 0, y: 18 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.65, delay: 0.08 } })} className="max-w-[650px] font-heading text-[clamp(3.2rem,7vw,6.1rem)] font-semibold leading-[.99] tracking-[-.065em]">
            Make sense of
            <span className="hero-gradient block">everything you know.</span>
          </motion.h1>
          <motion.p {...(reduceMotion ? {} : { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.6, delay: 0.18 } })} className="mt-7 max-w-[520px] text-base leading-8 text-atlas-slate sm:text-lg">
            Your documents hold the context. AtlasGPT helps you connect it, question it, and turn information into understanding.
          </motion.p>
          <motion.div {...(reduceMotion ? {} : { initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.55, delay: 0.26 } })} className="mt-9 flex flex-wrap items-center gap-3">
            <a href="/register" className="group inline-flex items-center gap-3 rounded-full bg-atlas-navy px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-atlas-navy/15 transition hover:-translate-y-0.5 hover:bg-atlas-deep-cyan">Create your workspace <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" /></a>
            <a href="#how-it-works" className="inline-flex items-center gap-2 rounded-full px-5 py-3.5 text-sm font-semibold text-atlas-slate transition hover:text-atlas-cyan">See how it works <ArrowDown size={15} /></a>
          </motion.div>
          <div className="mt-12 flex flex-wrap items-center gap-x-6 gap-y-3 border-t border-atlas-mist pt-6 text-xs font-medium text-atlas-slate">
            <span className="inline-flex items-center gap-2"><ShieldCheck size={15} className="text-atlas-cyan" /> Your own source material</span>
            <span className="inline-flex items-center gap-2"><Sparkles size={15} className="text-atlas-magenta" /> Built for deeper understanding</span>
          </div>
        </div>

        <motion.div {...(reduceMotion ? {} : { initial: { opacity: 0, scale: .96 }, animate: { opacity: 1, scale: 1 }, transition: { duration: .9, delay: .12 } })} className="hero-visual relative mx-auto flex w-full max-w-[620px] items-center justify-center">
          <div className="hero-halo absolute inset-[8%] rounded-full" />
          <div className="relative aspect-square w-full">
            <Suspense fallback={<div className="knowledge-orbit__fallback" />}>
              <KnowledgeOrbit />
            </Suspense>
            <div className="orbit-note orbit-note--top"><span className="orbit-note__dot" /> CONNECT IDEAS</div>
            <div className="orbit-note orbit-note--bottom">YOUR KNOWLEDGE, IN MOTION</div>
          </div>
        </motion.div>
      </section>

      <section className="border-y border-atlas-mist bg-atlas-cloud/70 px-6 py-7 lg:px-12">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 text-xs font-medium uppercase tracking-[.16em] text-atlas-slate">
          <span>Less searching</span><span className="hidden h-px flex-1 bg-atlas-mist sm:block" /><span>More connecting</span><span className="hidden h-px flex-1 bg-atlas-mist sm:block" /><span>Better questions</span><span className="hidden h-px flex-1 bg-atlas-mist sm:block" /><span>Clearer understanding</span>
        </div>
      </section>

      <section id="features" className="scroll-mt-24 px-6 py-24 sm:py-28 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <motion.div {...rise} className="max-w-2xl">
            <p className="section-kicker">A workspace for your thinking</p>
            <h2 className="section-heading">Not another place to store files.<br /><span className="text-atlas-slate">A better way to use them.</span></h2>
            <p className="mt-6 max-w-xl text-base leading-8 text-atlas-slate">AtlasGPT brings your material into the conversation, so you can spend less time hunting for information and more time understanding it.</p>
          </motion.div>
          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ icon: Icon, eyebrow, title, description, accent }, index) => (
              <motion.article key={eyebrow} {...rise} transition={{ duration: .5, delay: index * .07 }} whileHover={reduceMotion ? undefined : { y: -5 }} className="feature-card group rounded-2xl border border-atlas-mist bg-white p-6 sm:p-7">
                <div className={`feature-icon ${accent === 'magenta' ? 'feature-icon--magenta' : ''}`}><Icon size={21} strokeWidth={1.7} /></div>
                <p className="mt-8 text-[10px] font-bold tracking-[.18em] text-atlas-slate">{eyebrow}</p>
                <h3 className="mt-3 font-heading text-lg font-semibold tracking-tight">{title}</h3>
                <p className="mt-3 text-sm leading-7 text-atlas-slate">{description}</p>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="scroll-mt-24 bg-atlas-navy px-6 py-24 text-white sm:py-28 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <motion.div {...rise} className="grid gap-8 lg:grid-cols-[.8fr_1.2fr] lg:items-end">
            <div><p className="section-kicker section-kicker--dark">A simple process</p><h2 className="max-w-lg font-heading text-4xl font-semibold leading-tight tracking-[-.045em] sm:text-5xl">From scattered information to connected insight.</h2></div>
            <p className="max-w-xl text-sm leading-7 text-white/60 lg:justify-self-end">Your workflow stays simple. Bring your sources, give AtlasGPT a moment to index them, then ask the questions that move your work forward.</p>
          </motion.div>
          <div className="mt-16 grid gap-10 md:grid-cols-3 md:gap-8">
            {steps.map((step, index) => (
              <motion.article key={step.number} {...rise} transition={{ duration: .5, delay: index * .08 }} className="border-t border-white/20 pt-6">
                <span className="font-heading text-sm font-semibold text-[#D83995]">{step.number}</span>
                <h3 className="mt-7 font-heading text-xl font-semibold tracking-tight">{step.title}</h3>
                <p className="mt-3 max-w-sm text-sm leading-7 text-white/60">{step.description}</p>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      <section id="about" className="scroll-mt-24 px-6 py-24 sm:py-28 lg:px-12">
        <motion.div {...rise} className="mx-auto grid max-w-7xl gap-12 rounded-[2rem] border border-atlas-mist bg-atlas-cloud p-8 sm:p-12 lg:grid-cols-[1fr_.8fr] lg:items-center lg:p-16">
          <div><p className="section-kicker">Built around your sources</p><h2 className="section-heading">Your knowledge should work as hard as you do.</h2><p className="mt-6 max-w-xl text-base leading-8 text-atlas-slate">AtlasGPT is a document assistant for students, researchers and curious minds. It helps you revisit material, ask precise questions and build understanding from the information you bring.</p><a href="/register" className="mt-8 inline-flex items-center gap-3 rounded-full bg-atlas-cyan px-6 py-3.5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-atlas-deep-cyan">Start exploring <ArrowRight size={16} /></a></div>
          <div className="about-panel relative overflow-hidden rounded-2xl border border-atlas-mist bg-white p-6 sm:p-8"><div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-atlas-magenta/10 blur-3xl" /><div className="relative space-y-3"><div className="rounded-xl border border-atlas-mist bg-atlas-pearl p-4"><p className="text-[10px] font-bold uppercase tracking-[.18em] text-atlas-slate">SOURCE</p><p className="mt-2 text-sm font-semibold">Research-paper.pdf</p><p className="mt-1 text-xs text-atlas-slate">A collection of ideas and evidence</p></div><div className="flex justify-center text-atlas-cyan"><ArrowDown size={20} /></div><div className="rounded-xl border border-atlas-mist bg-atlas-pearl p-4"><p className="text-[10px] font-bold uppercase tracking-[.18em] text-atlas-magenta">CONTEXT</p><p className="mt-2 text-sm font-semibold">Relevant passages connected</p></div><div className="flex justify-center text-atlas-cyan"><ArrowDown size={20} /></div><div className="rounded-xl border border-atlas-cyan/30 bg-atlas-cyan/5 p-4"><p className="text-[10px] font-bold uppercase tracking-[.18em] text-atlas-deep-cyan">UNDERSTANDING</p><p className="mt-2 text-sm font-semibold">A useful answer, grounded in your source</p></div></div></div>
        </motion.div>
      </section>

      <section id="get-started" className="px-6 pb-24 lg:px-12">
        <motion.div {...rise} className="cta-panel mx-auto max-w-7xl rounded-[2rem] px-8 py-14 text-center sm:px-14 sm:py-20"><p className="section-kicker section-kicker--dark">Your next question starts here</p><h2 className="mx-auto mt-4 max-w-2xl font-heading text-4xl font-semibold tracking-[-.05em] text-white sm:text-5xl">Bring your knowledge together.</h2><p className="mx-auto mt-5 max-w-lg text-sm leading-7 text-white/65">Start with the documents you already have. See what you can discover when they become part of the conversation.</p><a href="/register" className="mt-8 inline-flex items-center gap-3 rounded-full bg-white px-6 py-3.5 text-sm font-semibold text-atlas-navy transition hover:-translate-y-0.5">Create your workspace <ArrowRight size={16} /></a></motion.div>
      </section>

      <footer className="border-t border-atlas-mist px-6 py-9 lg:px-12"><div className="mx-auto flex max-w-7xl flex-col justify-between gap-5 sm:flex-row sm:items-center"><a href="/" className="font-heading text-xl font-semibold tracking-tight">AtlasGPT<span className="text-[#D83995]">.</span><p className="mt-1 text-xs font-normal text-atlas-slate">Knowledge, beautifully connected.</p></a><div className="flex flex-wrap gap-6 text-xs font-medium text-atlas-slate"><a href="#features" className="hover:text-atlas-cyan">Features</a><a href="#how-it-works" className="hover:text-atlas-cyan">How it works</a><a href="#about" className="hover:text-atlas-cyan">About</a><a href="/login" className="hover:text-atlas-cyan">Sign in</a></div><p className="text-xs text-atlas-slate">© {new Date().getFullYear()} AtlasGPT</p></div></footer>
    </main>
  )
}

export default App
