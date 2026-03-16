'use client'

import { motion } from 'framer-motion'
import { ArrowUpRight } from 'lucide-react'
import { Navbar } from '@/components/navbar'
import { Footer } from '@/components/footer'

const papers = [
  {
    title: 'Energy-based Output Reward Model (EORM)',
    authors: 'Jiang et al.',
    year: '2025',
    venue: 'arXiv',
    description:
      'Primary architecture reference. Introduces the TransEBM architecture for scoring LLM outputs using energy functions with Bradley-Terry pairwise loss.',
    href: 'https://arxiv.org/abs/2505.14999',
    tags: ['Architecture', 'Core'],
  },
  {
    title: 'Iterative Refinement with Energy-based Decoding (IRED)',
    authors: 'Du et al.',
    year: '2024',
    venue: 'arXiv',
    description:
      'Guided decoding reference for V2 development. Demonstrates iterative refinement of LLM outputs using energy-based scoring.',
    href: 'https://arxiv.org/abs/2406.11179',
    tags: ['Decoding', 'V2'],
  },
  {
    title: 'Energy-Based Transformers (EBT)',
    authors: 'Gladstone et al.',
    year: '2025',
    venue: 'Conference',
    description:
      'Architecture vision for next-generation energy-based transformer models. Explores deeper integration of energy functions into the transformer architecture.',
    href: 'https://energy-based-transformers.github.io',
    tags: ['Architecture', 'V2'],
  },
  {
    title: 'Energy-Based Reward Model (EBRM)',
    authors: 'Lochab et al.',
    year: '2025',
    venue: 'arXiv',
    description:
      'Application of energy-based models to AI safety and RLHF replacement. Demonstrates constraint enforcement for safe AI outputs.',
    href: 'https://arxiv.org/abs/2504.13134',
    tags: ['Safety', 'RLHF'],
  },
]

export default function ResearchPage() {
  return (
    <>
      <Navbar />
      <main className="pt-32 pb-24">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
              Research
            </h1>
            <p className="text-lg text-neutral-500 mt-4 max-w-2xl leading-relaxed">
              Certainty Labs implements and extends peer-reviewed research in
              energy-based models for language model verification and constraint
              enforcement.
            </p>
          </motion.div>

          <div className="mt-16 space-y-6">
            {papers.map((paper, i) => (
              <motion.a
                key={paper.title}
                href={paper.href}
                target="_blank"
                rel="noopener noreferrer"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="block p-6 border border-neutral-200 rounded-lg hover:border-neutral-400 transition-all group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold group-hover:underline underline-offset-4">
                      {paper.title}
                    </h2>
                    <p className="text-sm text-neutral-500 mt-1">
                      {paper.authors} &middot; {paper.year} &middot;{' '}
                      {paper.venue}
                    </p>
                    <p className="text-sm text-neutral-600 mt-3 leading-relaxed">
                      {paper.description}
                    </p>
                    <div className="flex gap-2 mt-3">
                      {paper.tags.map((tag) => (
                        <span
                          key={tag}
                          className="text-xs font-mono px-2 py-0.5 rounded bg-neutral-100 text-neutral-500"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <ArrowUpRight className="w-5 h-5 text-neutral-300 group-hover:text-neutral-500 transition-colors shrink-0 mt-1" />
                </div>
              </motion.a>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mt-16 p-8 bg-neutral-50 rounded-lg border border-neutral-100"
          >
            <h3 className="text-lg font-semibold">Architecture overview</h3>
            <div className="mt-4 font-mono text-sm text-neutral-600 leading-relaxed">
              <pre>{`TransEBM Architecture
─────────────────────────
Model       Transformer from scratch (not finetuned)
Loss        Bradley-Terry: softplus(E_pos - E_neg)
Pooling     CLS token at position 0
Head        LayerNorm → Linear → GELU → Linear
Tokenizer   GPT-2 (tokenizer only, no pretrained weights)
Optimizer   AdamW (lr=5e-5), cosine warmup
Training    FP16 AMP, gradient clipping
Parameters  ~50M`}</pre>
            </div>
          </motion.div>
        </div>
      </main>
      <Footer />
    </>
  )
}
