'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { Navbar } from '@/components/navbar'
import { Footer } from '@/components/footer'
import { GridPattern } from '@/components/ui/grid-pattern'
import { Logos3 } from '@/components/blocks/logos3'
import { Feature } from '@/components/ui/feature-section-with-bento-grid'
import { TypingAnimation } from '@/components/ui/typing-animation'
import { Typewriter } from '@/components/ui/typewriter'
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@/components/ui/radix-accordion'
import { ArrowRight, Shield, Zap, Layers, Globe } from 'lucide-react'
import { cn } from '@/lib/utils'

const easeOutSmooth = [0.25, 0.46, 0.45, 0.94] as const

const fadeIn = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, ease: easeOutSmooth },
}

const fadeInUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: easeOutSmooth },
}

const stagger = {
  animate: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
}

const steps = [
  {
    step: '01',
    title: 'Provide data',
    desc: 'Send labeled examples that capture when your system is correct or incorrect.',
  },
  {
    step: '02',
    title: 'Train an energy model',
    desc: 'Train an EBM scorer so lower energy means more reliable, constraint-satisfying outputs.',
  },
  {
    step: '03',
    title: 'Score or rerank',
    desc: 'Call the API to score, rerank, or audit LLM outputs and find the most optimal candidate in milliseconds.',
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
        <section className="relative pt-500 md:pt-60 pb-16 px-6 overflow-hidden">
          <GridPattern
            width={40}
            height={40}
            x={-1}
            y={-1}
            className={cn(
              "[mask-image:radial-gradient(600px_ellipse_at_50%_0%,white_40%,transparent_70%)]",
              "inset-x-0 inset-y-[-20%] h-[140%]",
            )}
          />
          <div className="relative z-10 max-w-3xl mx-auto">
            <motion.div
              initial="initial"
              animate="animate"
              variants={stagger}
              className="space-y-8 text-center"
            >
              <motion.h1
                variants={fadeIn}
                className="font-serif text-4xl md:text-[2.75rem] leading-snug md:leading-snug font-semibold tracking-tight text-balance text-neutral-900"
              >
                The training API for model{' '}
                <Typewriter
                  words={[
                    'verification.',
                    'alignment.',
                    'constraints.',
                    'compliance.',
                  ]}
                  speed={55}
                  delayBetweenWords={1250}
                  cursor={true}
                  cursorChar="|"
                  className="inline-block min-w-[9ch]"
                />
              </motion.h1>
              <motion.p
                variants={fadeIn}
                className="font-serif text-base md:text-xl text-neutral-600 max-w-2xl mx-auto leading-relaxed"
              >
                Train custom Energy-Based Models that audit, score, and enforce logical alignment. You define the constraints. We handle everything else. 
              </motion.p>
              <motion.div
                variants={fadeInUp}
                className="flex flex-wrap items-center justify-center gap-4"
              >
                <Link
                  href="/platform"
                  className="inline-flex items-center gap-2 bg-neutral-900 text-white px-6 py-3 rounded-md text-sm font-medium hover:bg-neutral-800 transition-colors duration-300"
                >
                  Get started <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/research"
                  className="inline-flex items-center gap-2 text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors duration-300 px-6 py-3"
                >
                  Read the research
                </Link>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Logos / models banner */}
        <section className="border-y border-neutral-100">
          <Logos3 />
        </section>

        {/* How it works */}
        <section className="py-16 px-6">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.6, ease: easeOutSmooth }}
            >
              <h2 className="text-2xl md:text-3xl font-semibold tracking-tight font-mono">
                How it works
              </h2>
              <p className="text-neutral-500 mt-3 max-w-xl">
                Three steps to guaranteed outputs. All orchestrated through
                the API.
              </p>
            </motion.div>

            <motion.div
              className="grid md:grid-cols-3 gap-8 mt-10 items-stretch"
              variants={stagger}
              initial="initial"
              whileInView="animate"
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, ease: easeOutSmooth }}
            >
              {steps.map((item) => (
                <motion.div
                  key={item.step}
                  variants={fadeIn}
                  className="flex flex-col justify-start"
                >
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

        {/* Platform bento grid */}
        <section className="border-t border-neutral-100">
          <Feature />
        </section>

        {/* API */}
        <section className="py-24 px-6" id="api">
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.6, ease: easeOutSmooth }}
            >
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight font-mono">
                Simple, powerful API
              </h2>
              <p className="text-neutral-500 mt-3">
                Everything you need to enforce constraints on your model&apos;s
                outputs.
              </p>
            </motion.div>

            <motion.div
              className="mt-10 space-y-3"
              initial="initial"
              whileInView="animate"
              viewport={{ once: true, margin: "-40px" }}
              variants={stagger}
              transition={{ ease: easeOutSmooth }}
            >
              {[
                {
                  method: 'POST',
                  path: '/train',
                  desc: 'Train a TransEBM scorer on your data or the built-in dataset',
                },
                {
                  method: 'POST',
                  path: '/rerank',
                  desc: 'Score candidates and return the lowest-energy (best) output',
                },
                {
                  method: 'POST',
                  path: '/score',
                  desc: 'Get raw energy scores for any outputs without reranking',
                },
              ].map((ep) => (
                <motion.div
                  key={ep.path}
                  variants={fadeInUp}
                  className="flex items-center gap-4 p-4 border border-neutral-200 rounded-lg hover:border-neutral-300 transition-colors duration-300"
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
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, ease: easeOutSmooth }}
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
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.6, ease: easeOutSmooth }}
            >
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight font-mono">
                Research
              </h2>
              <p className="text-neutral-500 mt-3 max-w-xl">
                Built on peer-reviewed work in energy-based models for language
                model verification.
              </p>
            </motion.div>

            <motion.div
              className="grid md:grid-cols-2 gap-4 mt-12"
              initial="initial"
              whileInView="animate"
              viewport={{ once: true, margin: "-40px" }}
              variants={stagger}
              transition={{ ease: easeOutSmooth }}
            >
              {papers.map((paper) => (
                <motion.a
                  key={paper.title}
                  href={paper.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  variants={fadeInUp}
                  className="block p-5 border border-neutral-200 rounded-lg hover:border-neutral-400 transition-colors duration-300 group"
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
            </motion.div>
          </div>
        </section>

        {/* FAQ */}
        <section className="py-24 px-6 border-t border-neutral-100">
          <div className="max-w-2xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.6, ease: easeOutSmooth }}
            >
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight font-mono">
                Frequently asked questions
              </h2>
              <p className="text-neutral-500 mt-3">
                Quick answers about Energy-Based Models and the API.
              </p>
            </motion.div>

            <motion.div
              className="mt-10"
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.6, ease: easeOutSmooth }}
            >
              <Accordion
                type="single"
                defaultValue="item-1"
                collapsible
                className="w-full"
              >
                <AccordionItem value="item-1">
                  <AccordionTrigger>
                    What are Energy-Based Models?
                  </AccordionTrigger>
                  <AccordionContent>
                    Energy-Based Models (EBMs) assign a scalar energy score to
                    outputs. Lower energy means more reliable, constraint-satisfying
                    behavior. They work alongside any LLM to verify, score, and
                    rerank responses without retraining the base model.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="item-2">
                  <AccordionTrigger>
                    How is this different from prompt engineering?
                  </AccordionTrigger>
                  <AccordionContent>
                    Prompts are best-effort — they cannot guarantee outputs stay
                    inside your policy. EBMs provide a separate scorer that
                    verifies every response. You get constraint-guaranteed
                    behavior on critical paths, not just guidelines.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="item-3">
                  <AccordionTrigger>Is the API free to use?</AccordionTrigger>
                  <AccordionContent>
                    Get an API key to start. Usage is metered based on training
                    and scoring volume. Check the platform dashboard for pricing
                    and limits.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="item-4">
                  <AccordionTrigger>
                    Which language models are supported?
                  </AccordionTrigger>
                  <AccordionContent>
                    Any model. The EBM scorer operates independently of the
                    base LLM — you can use GPT-4o, Claude, Llama, Mistral, or any
                    provider. Swap models without rewriting your verification
                    rules.
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </motion.div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-24 px-6 bg-neutral-50">
          <motion.div
            className="max-w-2xl mx-auto text-center"
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6, ease: easeOutSmooth }}
          >
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              <TypingAnimation
                text="Start enforcing constraints"
                duration={80}
                inline
                className="text-3xl md:text-4xl font-bold tracking-tight font-mono"
              />
            </h2>
            <p className="text-neutral-500 mt-4 leading-relaxed">
              Get an API key and integrate constraint enforcement into your
              pipeline in minutes.
            </p>
            <motion.div
              className="flex items-center justify-center gap-4 mt-8"
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.15, ease: easeOutSmooth }}
            >
              <Link
                href="/platform"
                className="inline-flex items-center gap-2 bg-neutral-900 text-white px-6 py-3 rounded-md text-sm font-medium hover:bg-neutral-800 transition-colors duration-300"
              >
                Get started <ArrowRight className="w-4 h-4" />
              </Link>
            </motion.div>
          </motion.div>
        </section>
      </main>
      <Footer />
    </>
  )
}
