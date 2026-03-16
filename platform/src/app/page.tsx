'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { Navbar } from '@/components/navbar'
import { Footer } from '@/components/footer'
import { ArrowRight, Shield, Zap, Layers, Globe } from 'lucide-react'

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6 },
}

const stagger = {
  animate: { transition: { staggerChildren: 0.1 } },
}

const steps = [
  {
    step: '01',
    title: 'Define your rules',
    desc: 'Describe the constraints your outputs must satisfy — ranges, sums, conditions, allowed values, and more.',
  },
  {
    step: '02',
    title: 'Train a scorer',
    desc: 'A lightweight model learns to distinguish compliant outputs from non-compliant ones. Trains in minutes on a single GPU.',
  },
  {
    step: '03',
    title: 'Enforce at inference',
    desc: 'Every candidate output is scored automatically. The most compliant response is selected and returned.',
  },
]

const features = [
  {
    icon: Globe,
    title: 'Any model',
    desc: 'Works with GPT-4o, Claude, Llama, Mistral, or any language model. No vendor lock-in.',
  },
  {
    icon: Shield,
    title: 'No retraining',
    desc: 'Enforce constraints without modifying or retraining your base model. A separate scorer handles verification.',
  },
  {
    icon: Zap,
    title: 'Fast and lightweight',
    desc: 'The scoring model is ~50M parameters. Trains in minutes and runs inference in milliseconds.',
  },
  {
    icon: Layers,
    title: 'Simple API',
    desc: 'Three endpoints — compile, train, and rerank. Integrate into any pipeline with a few API calls.',
  },
]

const papers = [
  {
    title: 'EORM',
    authors: 'Jiang et al. 2025',
    desc: 'Energy-based Output Reward Model. Primary architecture reference.',
    href: 'https://arxiv.org/abs/2505.14999',
  },
  {
    title: 'IRED',
    authors: 'Du et al. 2024',
    desc: 'Iterative Refinement with Energy-based Decoding.',
    href: 'https://arxiv.org/abs/2406.11179',
  },
  {
    title: 'EBT',
    authors: 'Gladstone et al. 2025',
    desc: 'Energy-Based Transformers for next-generation scoring.',
    href: 'https://energy-based-transformers.github.io',
  },
  {
    title: 'EBRM',
    authors: 'Lochab et al. 2025',
    desc: 'Energy-Based Reward Models for AI safety.',
    href: 'https://arxiv.org/abs/2504.13134',
  },
]

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        {/* Hero */}
        <section className="pt-32 pb-24 px-6">
          <div className="max-w-3xl mx-auto">
            <motion.div {...fadeIn}>
              <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.05] text-balance">
                Constraint-guaranteed outputs for production AI
              </h1>
              <p className="text-xl text-neutral-500 mt-8 max-w-2xl leading-relaxed">
                Enforce hard constraints on any language model&apos;s output.
                Define your rules, and our system ensures every response
                satisfies them — through a simple API.
              </p>
              <div className="flex flex-wrap items-center gap-4 mt-10">
                <Link
                  href="/platform"
                  className="inline-flex items-center gap-2 bg-neutral-900 text-white px-6 py-3 rounded-md text-sm font-medium hover:bg-neutral-800 transition-colors"
                >
                  Get started <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/research"
                  className="inline-flex items-center gap-2 text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors px-6 py-3"
                >
                  Read the research
                </Link>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Compatible models */}
        <section className="py-10 border-y border-neutral-100">
          <div className="max-w-6xl mx-auto px-6">
            <div className="flex items-center justify-center gap-6 md:gap-10 flex-wrap text-neutral-400 text-sm">
              <span>GPT-4o</span>
              <span className="text-neutral-200 hidden md:inline">&middot;</span>
              <span>Claude</span>
              <span className="text-neutral-200 hidden md:inline">&middot;</span>
              <span>Llama 3</span>
              <span className="text-neutral-200 hidden md:inline">&middot;</span>
              <span>Mistral</span>
              <span className="text-neutral-200 hidden md:inline">&middot;</span>
              <span>Any LLM</span>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="py-24 px-6">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
                How it works
              </h2>
              <p className="text-neutral-500 mt-3 max-w-xl">
                Three steps to guaranteed outputs. All orchestrated through
                the API.
              </p>
            </motion.div>

            <motion.div
              className="grid md:grid-cols-3 gap-10 mt-16"
              variants={stagger}
              initial="initial"
              whileInView="animate"
              viewport={{ once: true }}
            >
              {steps.map((item) => (
                <motion.div key={item.step} variants={fadeIn}>
                  <span className="text-xs font-mono text-neutral-400">
                    {item.step}
                  </span>
                  <h3 className="text-lg font-semibold mt-2 mb-2">
                    {item.title}
                  </h3>
                  <p className="text-sm text-neutral-500 leading-relaxed">
                    {item.desc}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Why Certainty */}
        <section className="py-24 px-6 bg-neutral-950 text-white">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
                Built for production
              </h2>
              <p className="text-neutral-400 mt-3 max-w-xl leading-relaxed">
                A constraint enforcement layer that sits between your model and
                your users. No changes to your existing stack.
              </p>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8 mt-14">
              {features.map((f) => (
                <motion.div
                  key={f.title}
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4 }}
                  className="flex gap-4"
                >
                  <div className="p-2.5 bg-neutral-800 rounded-lg h-fit">
                    <f.icon className="w-4 h-4 text-neutral-400" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold">{f.title}</h3>
                    <p className="text-sm text-neutral-400 mt-1 leading-relaxed">
                      {f.desc}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* API */}
        <section className="py-24 px-6" id="api">
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
                Simple, powerful API
              </h2>
              <p className="text-neutral-500 mt-3">
                Everything you need to enforce constraints on your model&apos;s
                outputs.
              </p>
            </motion.div>

            <div className="mt-12 space-y-3">
              {[
                {
                  method: 'POST',
                  path: '/compile',
                  desc: 'Turn constraint definitions into a scoring function',
                },
                {
                  method: 'POST',
                  path: '/train',
                  desc: 'Train a scoring model from your data',
                },
                {
                  method: 'POST',
                  path: '/infer/rerank',
                  desc: 'Score candidates and return the best output',
                },
                {
                  method: 'POST',
                  path: '/pipeline',
                  desc: 'End-to-end: compile, train, and rerank in one call',
                },
              ].map((ep) => (
                <motion.div
                  key={ep.path}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4 }}
                  className="flex items-center gap-4 p-4 border border-neutral-200 rounded-lg hover:border-neutral-300 transition-colors"
                >
                  <span className="text-xs font-mono font-medium bg-neutral-100 text-neutral-600 px-2 py-1 rounded">
                    {ep.method}
                  </span>
                  <code className="text-sm font-mono font-medium">
                    {ep.path}
                  </code>
                  <span className="text-sm text-neutral-500 ml-auto hidden md:block">
                    {ep.desc}
                  </span>
                </motion.div>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="mt-6"
            >
              <Link
                href="/platform/docs"
                className="inline-flex items-center gap-2 text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors"
              >
                Full API reference <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </motion.div>
          </div>
        </section>

        {/* Research */}
        <section className="py-24 px-6 border-t border-neutral-100">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
                Research
              </h2>
              <p className="text-neutral-500 mt-3 max-w-xl">
                Built on peer-reviewed work in energy-based models for language
                model verification.
              </p>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-4 mt-12">
              {papers.map((paper) => (
                <motion.a
                  key={paper.title}
                  href={paper.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4 }}
                  className="block p-5 border border-neutral-200 rounded-lg hover:border-neutral-400 transition-colors group"
                >
                  <div className="flex items-baseline gap-2">
                    <h3 className="font-semibold font-mono">{paper.title}</h3>
                    <span className="text-xs text-neutral-400">
                      {paper.authors}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-500 mt-1.5">
                    {paper.desc}
                  </p>
                </motion.a>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-24 px-6 bg-neutral-50">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Start enforcing constraints
            </h2>
            <p className="text-neutral-500 mt-4 leading-relaxed">
              Get an API key and integrate constraint enforcement into your
              pipeline in minutes.
            </p>
            <div className="flex items-center justify-center gap-4 mt-8">
              <Link
                href="/platform"
                className="inline-flex items-center gap-2 bg-neutral-900 text-white px-6 py-3 rounded-md text-sm font-medium hover:bg-neutral-800 transition-colors"
              >
                Get started <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
