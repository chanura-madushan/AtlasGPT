import { lazy, Suspense } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { ArrowRight, ArrowUpRight, BookOpen, FileText, MessageSquareText, Search, ShieldCheck, Waypoints } from 'lucide-react'
import Navbar from './components/navigation/Navbar'

const KnowledgeAtlas = lazy(() => import('./components/visuals/KnowledgeAtlas'))

const capabilities = [
  { number: '01', icon: FileText, title: 'Bring your material', description: 'PDFs, Word documents and text files become part of one private knowledge space.' },
  { number: '02', icon: Search, title: 'Find the relevant detail', description: 'AtlasGPT retrieves useful passages from your own sources before it answers.' },
  { number: '03', icon: MessageSquareText, title: 'Think in conversation', description: 'Ask follow-up questions and return to previous conversations without losing context.' },
]

function App() {
  const reduceMotion = useReducedMotion()
  const reveal = reduceMotion ? {} : { initial: { opacity: 0, y: 22 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, amount: 0.2 }, transition: { duration: 0.65, ease: [0.22, 1, 0.36, 1] as const } }

  return (
    <main className="atlas-site">
      <Navbar />
      <section className="atlas-hero">
        <div className="atlas-hero__grid" aria-hidden="true" />
        <div className="atlas-hero__copy">
          <div className="atlas-eyebrow"><span className="atlas-eyebrow__mark" /> A workspace built around your sources</div>
          <h1>Make your<br /><em>knowledge</em><br />go further.</h1>
          <p className="atlas-hero__lead">A focused place to bring your documents, ask better questions, and understand what matters — with answers grounded in the material you provide.</p>
          <div className="atlas-hero__actions">
            <a href="/register" className="atlas-button atlas-button--primary">Create your workspace <ArrowRight size={17} /></a>
            <a href="#method" className="atlas-text-link">Explore the method <ArrowUpRight size={16} /></a>
          </div>
          <div className="atlas-hero__proof">
            <span><ShieldCheck size={15} /> Your sources stay yours</span>
            <span><BookOpen size={15} /> Built for study and research</span>
          </div>
        </div>
        <div className="atlas-hero__visual">
          <div className="atlas-visual-frame">
            <div className="atlas-visual-frame__top"><span>ATLAS / FIELD MAP</span><span>01 — 03</span></div>
            <div className="atlas-visual-frame__scene">
              <Suspense fallback={<div className="atlas-scene-loading" />}>
                <KnowledgeAtlas />
              </Suspense>
              <div className="atlas-map-label atlas-map-label--north"><span className="atlas-map-label__pin" /> SOURCE 01 <b>Research notes</b></div>
              <div className="atlas-map-label atlas-map-label--east"><span className="atlas-map-label__pin atlas-map-label__pin--pink" /> SOURCE 02 <b>Lecture material</b></div>
              <div className="atlas-map-label atlas-map-label--south">CONNECTED CONTEXT <span>↗</span></div>
            </div>
            <div className="atlas-visual-frame__bottom"><span>DOCUMENTS → CONTEXT → UNDERSTANDING</span><span className="atlas-live-mark">● INDEXED VIEW</span></div>
          </div>
          <div className="atlas-hero__caption">A map of what you know — not another blank chat window.</div>
        </div>
        <div className="atlas-hero__index" aria-hidden="true"><span>ATLASGPT</span><span>01 / YOUR KNOWLEDGE, MAPPED</span></div>
      </section>

      <section className="atlas-manifesto">
        <div className="atlas-manifesto__inner">
          <p className="atlas-section-label">THE IDEA</p>
          <h2>Your documents are not the destination.<br /><span>They are where better questions begin.</span></h2>
          <p>AtlasGPT turns the material you already have into a space you can explore. No invented library. No claims of certainty. Just your sources, made easier to work with.</p>
        </div>
        <div className="atlas-manifesto__side"><Waypoints size={24} /><span>01 — 03</span><small>COLLECT / CONNECT / UNDERSTAND</small></div>
      </section>

      <section id="features" className="atlas-capabilities">
        <div className="atlas-section-head" {...reveal}>
          <p className="atlas-section-label">A CLEARER WORKFLOW</p>
          <h2>Less hunting.<br /><span>More understanding.</span></h2>
        </div>
        <div className="atlas-capabilities__list">
          {capabilities.map(({ number, icon: Icon, title, description }, index) => (
            <motion.article key={number} {...reveal} transition={{ duration: 0.55, delay: index * 0.08 }} className="atlas-capability">
              <span className="atlas-capability__number">{number}</span>
              <span className="atlas-capability__icon"><Icon size={21} strokeWidth={1.6} /></span>
              <div><h3>{title}</h3><p>{description}</p></div>
              <ArrowUpRight className="atlas-capability__arrow" size={20} />
            </motion.article>
          ))}
        </div>
      </section>

      <section id="method" className="atlas-method">
        <div className="atlas-method__head" {...reveal}>
          <p className="atlas-section-label">THREE STEPS, ONE WORKSPACE</p>
          <h2>From source material<br />to <em>clearer thinking.</em></h2>
        </div>
        <div className="atlas-method__steps">
          <article><span>01</span><h3>Collect</h3><p>Add PDFs, DOCX or text files to your private workspace.</p></article>
          <article><span>02</span><h3>Connect</h3><p>AtlasGPT indexes your documents and retrieves relevant passages.</p></article>
          <article><span>03</span><h3>Explore</h3><p>Ask questions, follow the thread and revisit past conversations.</p></article>
        </div>
        <div className="atlas-method__foot"><span>DESIGNED FOR STUDENTS, RESEARCHERS & CURIOUS MINDS</span><span>ATLASGPT / 2026</span></div>
      </section>

      <section className="atlas-final">
        <div className="atlas-final__rule" />
        <p className="atlas-section-label">YOUR NEXT QUESTION</p>
        <h2>Start with what<br /><em>you already know.</em></h2>
        <a href="/register" className="atlas-button atlas-button--light">Build your knowledge space <ArrowRight size={17} /></a>
        <span className="atlas-final__coordinates">06° 55' N / 79° 51' E — KNOWLEDGE HAS NO BOUNDARIES</span>
      </section>

      <footer className="atlas-footer">
        <a href="/" className="atlas-footer__brand">ATLAS<span>GPT</span><i>®</i></a>
        <p>Knowledge, beautifully connected.</p>
        <div><a href="#features">Features</a><a href="#method">How it works</a><a href="/login">Sign in</a></div>
        <small>© 2026 ATLASGPT. BUILT AROUND YOUR SOURCES.</small>
      </footer>
    </main>
  )
}

export default App
