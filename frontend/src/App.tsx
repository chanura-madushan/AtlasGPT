
import Navbar from './components/navigation/Navbar'
import heroImage from './assets/hero.png'

import {
  FileText,
  MessageSquare,
  Search,
  History,
} from 'lucide-react'

function App() {
  return (
<main className="min-h-screen overflow-x-hidden bg-atlas-pearl pt-[81px] text-atlas-navy">      <Navbar />

      {/* Hero section */}
      <section className="relative mx-auto grid min-h-[85vh] max-w-7xl items-center gap-12 px-6 py-20 lg:grid-cols-2 lg:px-12">
        <div className="z-10">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-atlas-mist bg-white px-4 py-2 text-sm text-atlas-deep-cyan">
            <span className="h-2 w-2 rounded-full bg-atlas-cyan" />
            Your personal AI knowledge assistant
          </div>

          <h1 className="max-w-xl font-heading text-5xl font-bold leading-tight tracking-tight sm:text-6xl lg:text-7xl">
            Your knowledge.
            <span className="block text-atlas-cyan">
              Connected.
            </span>
          </h1>

          <p className="mt-6 max-w-lg text-base leading-8 text-atlas-slate sm:text-lg">
            Bring your documents together, ask meaningful questions,
            and discover insights with an AI assistant grounded in
            your own knowledge.
          </p>

          <div className="mt-9 flex flex-wrap items-center gap-4">
            <a
              href="#get-started"
              className="rounded-xl bg-atlas-cyan px-7 py-3.5 font-semibold text-white transition hover:bg-atlas-deep-cyan"
            >
              Get started
            </a>

            <a
              href="#features"
              className="rounded-xl border border-atlas-mist bg-white px-7 py-3.5 font-semibold text-atlas-navy transition hover:border-atlas-cyan hover:text-atlas-deep-cyan"
            >
              Explore features
            </a>
          </div>

          <p className="mt-6 text-sm text-atlas-slate">
            Your documents. Your knowledge. Your answers.
          </p>
        </div>

        {/* Hero visual */}
        <div className="relative flex items-center justify-center">
          <div className="absolute h-72 w-72 rounded-full bg-atlas-cyan/10 blur-3xl sm:h-96 sm:w-96" />

          <img
            src={heroImage}
            alt="Abstract AtlasGPT knowledge visualization"
            className="relative z-10 w-full max-w-lg object-contain"
          />
        </div>
      </section>

      {/* Features section */}
      <section
        id="features"
        className="bg-atlas-cloud px-6 py-24 lg:px-12"
      >
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-atlas-cyan">
              What AtlasGPT offers
            </p>

            <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl">
              Everything you need to understand your documents.
            </h2>

            <p className="mt-5 leading-7 text-atlas-slate">
              Turn scattered documents into a connected knowledge
              space. Find information, ask questions, and keep
              your conversations grounded in your sources.
            </p>
          </div>

          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <article className="rounded-2xl border border-atlas-mist bg-white p-7 transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-atlas-navy/5">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-atlas-cyan/10 text-atlas-deep-cyan">
                <FileText size={24} strokeWidth={1.8} />
              </div>

              <h3 className="mt-6 font-heading text-lg font-bold">
                Document intelligence
              </h3>

              <p className="mt-3 text-sm leading-7 text-atlas-slate">
                Upload PDF, TXT, and DOCX files and let AtlasGPT
                process their content.
              </p>
            </article>

            <article className="rounded-2xl border border-atlas-mist bg-white p-7 transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-atlas-navy/5">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-atlas-magenta/10 text-atlas-magenta">
                <MessageSquare size={24} strokeWidth={1.8} />
              </div>

              <h3 className="mt-6 font-heading text-lg font-bold">
                Context-aware chat
              </h3>

              <p className="mt-3 text-sm leading-7 text-atlas-slate">
                Ask questions and receive answers informed by the
                content of your documents.
              </p>
            </article>

            <article className="rounded-2xl border border-atlas-mist bg-white p-7 transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-atlas-navy/5">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-atlas-cyan/10 text-atlas-deep-cyan">
                <Search size={24} strokeWidth={1.8} />
              </div>

              <h3 className="mt-6 font-heading text-lg font-bold">
                Source-backed answers
              </h3>

              <p className="mt-3 text-sm leading-7 text-atlas-slate">
                Connect answers to relevant document sources instead
                of relying on unsupported claims.
              </p>
            </article>

            <article className="rounded-2xl border border-atlas-mist bg-white p-7 transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-atlas-navy/5">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-atlas-magenta/10 text-atlas-magenta">
                <History size={24} strokeWidth={1.8} />
              </div>

              <h3 className="mt-6 font-heading text-lg font-bold">
                Conversation history
              </h3>

              <p className="mt-3 text-sm leading-7 text-atlas-slate">
                Continue previous conversations and keep track of
                your knowledge discoveries.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* How it works section */}
      <section
        id="how-it-works"
        className="bg-atlas-pearl px-6 py-24 lg:px-12"
      >
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-atlas-cyan">
              A simple workflow
            </p>

            <h2 className="mt-4 font-heading text-3xl font-bold tracking-tight sm:text-4xl">
              From documents to discoveries.
            </h2>

            <p className="mt-5 leading-7 text-atlas-slate">
              Your knowledge journey starts with three simple steps.
            </p>
          </div>

          <div className="relative mt-20 grid gap-12 md:grid-cols-3 md:gap-8">
            {[
              {
                number: '01',
                title: 'Upload your documents',
                description:
                  'Bring your PDF, TXT and DOCX files into one organized knowledge space.',
              },
              {
                number: '02',
                title: 'Let AtlasGPT understand',
                description:
                  'Your documents are processed, divided into meaningful chunks and indexed for retrieval.',
              },
              {
                number: '03',
                title: 'Ask and discover',
                description:
                  'Ask natural-language questions and explore answers grounded in your uploaded sources.',
              },
            ].map((step) => (
              <article key={step.number} className="relative text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-atlas-cyan/10 font-heading text-xl font-bold text-atlas-deep-cyan">
                  {step.number}
                </div>

                <h3 className="mt-7 font-heading text-xl font-bold">
                  {step.title}
                </h3>

                <p className="mx-auto mt-4 max-w-sm text-sm leading-7 text-atlas-slate">
                  {step.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* About section */}
      <section
        id="about"
        className="bg-atlas-cloud px-6 py-24 lg:px-12"
      >
        <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-2">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-atlas-cyan">
              About AtlasGPT
            </p>

            <h2 className="mt-4 max-w-xl font-heading text-3xl font-bold leading-tight tracking-tight sm:text-4xl">
              Your knowledge deserves more than a search bar.
            </h2>

            <p className="mt-6 max-w-xl leading-8 text-atlas-slate">
              AtlasGPT is a local-first AI document assistant
              designed to help you understand information in
              your own documents.
            </p>

            <p className="mt-4 max-w-xl leading-8 text-atlas-slate">
              Instead of searching through pages manually,
              you can ask questions, explore relevant context,
              and continue meaningful conversations with your
              knowledge.
            </p>

            <a
              href="#get-started"
              className="mt-8 inline-flex rounded-xl bg-atlas-cyan px-7 py-3.5 font-semibold text-white transition hover:bg-atlas-deep-cyan"
            >
              Explore AtlasGPT
            </a>
          </div>

          <div className="relative flex min-h-80 items-center justify-center overflow-hidden rounded-3xl border border-atlas-mist bg-white p-10">
            <div className="absolute h-64 w-64 rounded-full bg-atlas-cyan/10 blur-3xl" />

            <div className="relative w-full max-w-sm space-y-4">
              <div className="rounded-2xl border border-atlas-mist bg-atlas-pearl p-5 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wider text-atlas-cyan">
                  Your documents
                </p>
                <p className="mt-2 font-heading font-semibold">
                  Research.pdf
                </p>
              </div>

              <div className="flex justify-center text-2xl text-atlas-cyan">
                ↓
              </div>

              <div className="rounded-2xl border border-atlas-mist bg-atlas-pearl p-5 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wider text-atlas-magenta">
                  AtlasGPT
                </p>
                <p className="mt-2 font-heading font-semibold">
                  Knowledge connected.
                </p>
              </div>

              <div className="flex justify-center text-2xl text-atlas-cyan">
                ↓
              </div>

              <div className="rounded-2xl border border-atlas-mist bg-atlas-pearl p-5 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wider text-atlas-cyan">
                  Your insight
                </p>
                <p className="mt-2 font-heading font-semibold">
                  Answers grounded in your sources.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-atlas-navy px-6 py-12 text-white lg:px-12">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-8 sm:flex-row sm:items-center">
          <div>
            <a
              href="/"
              className="font-heading text-2xl font-bold tracking-tight"
            >
              AtlasGPT
              <span className="text-atlas-cyan">.</span>
            </a>

            <p className="mt-3 text-sm text-white/60">
              Knowledge, beautifully connected.
            </p>
          </div>

          <div className="flex flex-wrap gap-6 text-sm text-white/70">
            <a href="#features" className="transition hover:text-white">
              Features
            </a>
            <a href="#how-it-works" className="transition hover:text-white">
              How it works
            </a>
            <a href="#about" className="transition hover:text-white">
              About
            </a>
          </div>
        </div>

        <div className="mx-auto mt-10 max-w-7xl border-t border-white/10 pt-6 text-sm text-white/50">
          © {new Date().getFullYear()} AtlasGPT. All rights reserved.
        </div>
      </footer>
    </main>
  )
}

export default App
