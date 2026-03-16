"""
Certainty Labs -- Streamlit Demo Application

A polished, four-tab interface for the constraint enforcement runtime.
Designed for both technical demos and investor presentations.
"""

import streamlit as st
import os
import sys
import json
import time
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(
    page_title="Certainty Labs",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for polished look ─────────────────────────────────────

st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .metric-card {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        border: 1px solid #2A2A4E;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #6C5CE7;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #A0A0C0;
        margin-top: 4px;
    }
    .success-banner {
        background: linear-gradient(90deg, #00b09433, #96c93d33);
        border: 1px solid #00b09466;
        border-radius: 8px;
        padding: 12px 20px;
        margin: 10px 0;
    }
    div[data-testid="stTabs"] button {
        font-size: 1rem;
        font-weight: 600;
    }
    .stCodeBlock {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────

st.markdown("# Certainty Labs")
st.markdown(
    "**Constraint-Guaranteed Outputs for Production AI** "
    "-- powered by Energy-Based Models (EORM architecture)"
)
st.markdown("---")


def _demo_energy_fn(parsed):
    """Simple energy for demo: portfolio (weights sum to 1) or generic."""
    if not isinstance(parsed, dict):
        return 100.0
    if "weights" in parsed:
        try:
            total = sum(float(v) for v in parsed["weights"].values())
            return 0.0 if abs(total - 1.0) < 0.01 else 10.0 * abs(total - 1.0)
        except (TypeError, ValueError):
            return 10.0
    return 0.0


# ── Tabs ─────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview & Data Format",
    "Prepare Data",
    "Train Model",
    "Evaluate & Rerank",
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW & DATA FORMAT
# ═══════════════════════════════════════════════════════════════════

with tab1:
    st.subheader("Overview & EORM Data Format")
    st.markdown(
        "Certainty trains a TransEBM on **your data** (or the built-in GSM8K dataset). "
        "Training data must be **EORM format**: one JSON object per line with `question`, `label` (0 or 1), and `gen_text`."
    )
    st.markdown("**Generating your own data:** Use your own pipeline (e.g. your LLM + rules or model-as-judge) to assign label 0/1 per (question, gen_text). Export as JSONL and upload in **Prepare Data** or use the built-in dataset.")
    st.code(
        '{"question": "What is 2+2?", "label": 1, "gen_text": "The answer is 4."}\n'
        '{"question": "What is 2+2?", "label": 0, "gen_text": "The answer is 5."}',
        language="jsonl",
    )
    st.session_state["energy_fn"] = _demo_energy_fn  # used by "Generate with Mock Sampler" in Tab 2


# ═══════════════════════════════════════════════════════════════════
# TAB 2: PREPARE DATA
# ═══════════════════════════════════════════════════════════════════

with tab2:
    st.subheader("Prepare Training Data")
    st.markdown(
        "Generate labeled data using an LLM, upload your own, or use the default "
        "EORM demo dataset (GSM8K-Llama)."
    )

    data_source = st.radio(
        "Data source",
        [
            "EORM Demo Dataset (GSM8K-Llama)",
            "Generate with Mock Sampler",
            "Upload your data (JSONL/CSV/JSON)",
        ],
        horizontal=True,
    )

    if data_source == "EORM Demo Dataset (GSM8K-Llama)":
        st.markdown(
            "Uses the default EORM dataset files from "
            "[EnergyORM](https://github.com/ericjiang18/EnergyORM):"
        )

        demo_dir = os.path.join(os.path.dirname(__file__), "..", "demo_dataset")
        train_file = os.path.join(
            demo_dir,
            "results_gsm8k_llama3_train_n4_temp0.7_p0.9_train (2).jsonl",
        )
        test_file = os.path.join(
            demo_dir,
            "results_gsm8k_llama3_test_n4_temp0.7_p0.9_test (2).jsonl",
        )

        st.code(
            "demo_dataset/\n"
            "  results_gsm8k_llama3_train_n4_temp0.7_p0.9_train (2).jsonl\n"
            "  results_gsm8k_llama3_test_n4_temp0.7_p0.9_test (2).jsonl",
            language="text",
        )

        if os.path.exists(train_file):
            line_count = sum(1 for _ in open(train_file))
            st.success(f"Train file found: {line_count} lines")
            st.session_state["data_path"] = train_file
            st.session_state["data_source"] = "eorm_demo"
        else:
            st.warning(
                "Demo dataset not found. Download from the "
                "[EnergyORM README](https://github.com/ericjiang18/EnergyORM#3-download-demo-datasets) "
                "and place the JSONL files in the `demo_dataset/` directory."
            )
            st.info(
                "If no data is provided, the trainer will attempt to locate the "
                "demo dataset automatically."
            )
            st.session_state["data_path"] = None
            st.session_state["data_source"] = "eorm_demo"

    elif data_source == "Generate with Mock Sampler":
        col1, col2 = st.columns(2)
        with col1:
            n_samples = st.slider("Number of samples", 50, 2000, 500, step=50)
            domain = st.selectbox("Domain", ["portfolio", "dosage", "generic"])
        with col2:
            prompt = st.text_area(
                "Prompt",
                value="Generate a valid portfolio allocation as JSON with weights for 3-5 stocks.",
                height=100,
            )

        if st.button("Generate Data", type="primary", key="gen_data"):
            energy_fn = st.session_state.get("energy_fn", _demo_energy_fn)
            if callable(energy_fn):
                with st.status("Generating training data...", expanded=True) as status:
                    from certainty.data.sampler import MockSampler
                    from certainty.data.generator import DataGenerator, GeneratorConfig

                    sampler = MockSampler(domain=domain)
                    gen_config = GeneratorConfig(n_samples=n_samples)
                    gen = DataGenerator(energy_fn, sampler, gen_config)

                    output_dir = str(Path("certainty_workspace"))
                    os.makedirs(output_dir, exist_ok=True)

                    st.write("Sampling candidates...")
                    raw = sampler.sample(prompt, n=n_samples)

                    st.write("Labeling with energy function...")
                    from certainty.data.labeler import SymbolicLabeler
                    labeler = SymbolicLabeler(energy_fn)
                    labeled = labeler.label_all(raw)

                    positives = [x for x in labeled if x["label"] == "positive"]
                    negatives = [x for x in labeled if x["label"] == "negative"]
                    ambiguous = [x for x in labeled if x["label"] == "ambiguous"]

                    if len(negatives) < 200 and positives:
                        st.write("Synthesizing additional negatives...")
                        from certainty.data.negatives import NegativeSynthesizer
                        synth = NegativeSynthesizer(energy_fn)
                        synthetic = synth.synthesize(positives, n_needed=200 - len(negatives))
                        negatives.extend(synthetic)

                    status.update(label="Data generation complete", state="complete")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Sampled", len(labeled))
                m2.metric("Positives", len(positives))
                m3.metric("Negatives", len(negatives))
                m4.metric("Ambiguous", len(ambiguous))

                energies_pos = [x["energy"] for x in positives if x["energy"] != float("inf")]
                energies_neg = [x["energy"] for x in negatives if x["energy"] != float("inf")]

                if energies_pos or energies_neg:
                    import plotly.graph_objects as go

                    fig = go.Figure()
                    if energies_pos:
                        fig.add_trace(go.Histogram(
                            x=energies_pos, name="Valid (positive)",
                            marker_color="#00b894", opacity=0.7, nbinsx=30,
                        ))
                    if energies_neg:
                        fig.add_trace(go.Histogram(
                            x=energies_neg, name="Violations (negative)",
                            marker_color="#e17055", opacity=0.7, nbinsx=30,
                        ))
                    fig.update_layout(
                        title="Energy Distribution",
                        xaxis_title="Energy Score",
                        yaxis_title="Count",
                        barmode="overlay",
                        template="plotly_dark",
                        height=350,
                        margin=dict(t=40, b=40),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                eorm_records = []
                for item in positives:
                    eorm_records.append({"question": prompt, "label": 1, "gen_text": item["text"]})
                for item in negatives:
                    eorm_records.append({"question": prompt, "label": 0, "gen_text": item["text"]})

                data_path = os.path.join("certainty_workspace", "training_data.jsonl")
                os.makedirs("certainty_workspace", exist_ok=True)
                import jsonlines
                with jsonlines.open(data_path, mode="w") as w:
                    w.write_all(eorm_records)

                st.session_state["data_path"] = data_path
                st.session_state["data_records"] = eorm_records
                st.session_state["data_source"] = "generated"
                st.toast("Training data saved", icon="disk")

    else:
        uploaded_data = st.file_uploader(
            "Upload data file",
            type=["jsonl", "csv", "json"],
            help="JSONL format: each line = {\"question\": ..., \"label\": 0|1, \"gen_text\": ...}",
        )
        if uploaded_data:
            content = uploaded_data.read().decode("utf-8")
            records = []
            if uploaded_data.name.endswith(".jsonl"):
                for line in content.splitlines():
                    if line.strip():
                        records.append(json.loads(line))
            elif uploaded_data.name.endswith(".json"):
                data = json.loads(content)
                records = data if isinstance(data, list) else [data]
            elif uploaded_data.name.endswith(".csv"):
                import csv as csv_mod
                import io
                reader = csv_mod.DictReader(io.StringIO(content))
                for row in reader:
                    row["label"] = int(row.get("label", 0))
                    records.append(row)

            if records:
                st.success(f"Loaded {len(records)} records from {uploaded_data.name}")

                data_path = os.path.join("certainty_workspace", "training_data.jsonl")
                os.makedirs("certainty_workspace", exist_ok=True)
                import jsonlines
                with jsonlines.open(data_path, mode="w") as w:
                    w.write_all(records)

                st.session_state["data_path"] = data_path
                st.session_state["data_records"] = records
                st.session_state["data_source"] = "uploaded"

                labels = [r.get("label", -1) for r in records]
                c1, c2 = st.columns(2)
                c1.metric("Positive (label=1)", sum(1 for l in labels if l == 1))
                c2.metric("Negative (label=0)", sum(1 for l in labels if l == 0))

                with st.expander("Preview data"):
                    for r in records[:5]:
                        st.json(r)


# ═══════════════════════════════════════════════════════════════════
# TAB 3: TRAIN MODEL
# ═══════════════════════════════════════════════════════════════════

with tab3:
    st.subheader("Train TransEBM")
    st.markdown(
        "Train a lightweight Transformer energy model using the EORM architecture. "
        "Optimized for Kaggle T4 GPU (16GB VRAM) with FP16 mixed precision."
    )

    col_config, col_status = st.columns([1, 2], gap="large")

    with col_config:
        st.markdown("**Training Configuration**")
        epochs = st.slider("Epochs", 5, 50, 20)
        lr = st.select_slider(
            "Learning rate",
            options=[1e-5, 2e-5, 5e-5, 1e-4, 2e-4],
            value=5e-5,
            format_func=lambda x: f"{x:.0e}",
        )
        d_model = st.selectbox("Model dimension", [256, 512, 768], index=2)
        n_layers = st.selectbox("Transformer layers", [1, 2, 3, 4], index=1)
        from certainty.models.supported_models import TOKENIZER_ALIASES
        tokenizer_options = ["gpt2"] + [k for k in TOKENIZER_ALIASES if k != "gpt2"]
        tokenizer_display = {k: k if k == "gpt2" else f"{k} (Qwen/Llama)" for k in tokenizer_options}
        tokenizer_choice = st.selectbox(
            "Tokenizer (match your LLM for Qwen/Llama)",
            options=tokenizer_options,
            format_func=lambda x: tokenizer_display.get(x, x),
            index=0,
        )
        validate_every = st.slider("Validate every N epochs", 1, 5, 1)

        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1e9
            st.success(f"GPU: {gpu_name} ({gpu_mem:.1f} GB)")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            st.info("Device: Apple Silicon (MPS)")
        else:
            st.warning("No GPU detected -- training will use CPU")

        data_source_info = st.session_state.get("data_source", "none")
        data_path = st.session_state.get("data_path")
        if data_source_info == "eorm_demo":
            st.info("Data: EORM demo dataset (GSM8K-Llama)")
        elif data_source_info == "generated":
            st.info("Data: Generated with Mock Sampler")
        elif data_source_info == "uploaded":
            st.info("Data: User-uploaded file")
        else:
            st.info(
                "No data selected. Trainer will fall back to default EORM "
                "demo dataset if available."
            )

        train_btn = st.button("Start Training", type="primary", key="train_btn")

    with col_status:
        if train_btn:
            data_path = st.session_state.get("data_path")

            progress_bar = st.progress(0, text="Initializing...")
            loss_chart_placeholder = st.empty()
            metrics_placeholder = st.empty()

            loss_history = []
            acc_history = []

            def on_epoch(epoch, loss, val_acc):
                loss_history.append(loss)
                acc_history.append(val_acc)
                pct = epoch / epochs
                progress_bar.progress(pct, text=f"Epoch {epoch}/{epochs} | Loss: {loss:.4f}")

                import plotly.graph_objects as go
                from plotly.subplots import make_subplots

                fig = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=("Training Loss", "Validation Accuracy"),
                )
                fig.add_trace(
                    go.Scatter(
                        y=loss_history, mode="lines+markers",
                        line=dict(color="#6C5CE7", width=2),
                        marker=dict(size=4),
                    ),
                    row=1, col=1,
                )
                fig.add_trace(
                    go.Scatter(
                        y=acc_history, mode="lines+markers",
                        line=dict(color="#00b894", width=2),
                        marker=dict(size=4),
                    ),
                    row=1, col=2,
                )
                fig.update_layout(
                    template="plotly_dark",
                    height=300,
                    showlegend=False,
                    margin=dict(t=30, b=30),
                )
                fig.update_xaxes(title_text="Epoch", row=1, col=1)
                fig.update_xaxes(title_text="Epoch", row=1, col=2)
                fig.update_yaxes(title_text="Loss", row=1, col=1)
                fig.update_yaxes(title_text="Accuracy %", row=1, col=2)
                loss_chart_placeholder.plotly_chart(fig, use_container_width=True)

            with st.status("Training TransEBM...", expanded=True) as status:
                from certainty.models.trainer import EBMTrainer, TrainingConfig
                from certainty.models.supported_models import resolve_tokenizer_name

                config = TrainingConfig(
                    tokenizer_name=resolve_tokenizer_name(tokenizer_choice),
                    epochs=epochs,
                    lr=lr,
                    d_model=d_model,
                    n_layers=n_layers,
                    validate_every=validate_every,
                )
                trainer = EBMTrainer(config)
                st.write(f"Device: {trainer.device}")
                st.write(f"Model: TransEBM (d={d_model}, layers={n_layers})")

                output_dir = str(Path("certainty_workspace") / "model")
                metrics = trainer.train(
                    data_path=data_path,
                    output_dir=output_dir,
                    progress_callback=on_epoch,
                )
                status.update(label="Training complete", state="complete")

            progress_bar.progress(1.0, text="Training complete")

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Best Val Accuracy", f"{metrics['best_val_acc']:.1f}%")
            r2.metric("Final Loss", f"{metrics['final_loss']:.4f}")
            r3.metric("Epochs", metrics["epochs_trained"])
            r4.metric("Time", f"{metrics['elapsed_seconds']:.0f}s")

            st.session_state["model_path"] = metrics["model_path"]
            st.session_state["tokenizer_path"] = metrics["tokenizer_path"]
            st.toast("Model saved", icon="disk")

        else:
            st.info(
                "Configure training parameters and click **Start Training**. "
                "Make sure you have prepared data in Tab 2, or use the default "
                "EORM demo dataset."
            )


# ═══════════════════════════════════════════════════════════════════
# TAB 4: EVALUATE & RERANK
# ═══════════════════════════════════════════════════════════════════

with tab4:
    st.subheader("Evaluate & Rerank")
    st.markdown(
        "Score candidate outputs with the trained TransEBM and select "
        "the most constraint-satisfying one."
    )

    model_path = st.session_state.get("model_path")
    tokenizer_path = st.session_state.get("tokenizer_path")

    if not model_path or not os.path.exists(str(model_path)):
        st.info(
            "No trained model found. Train a model in Tab 3, or enter a model path below."
        )
        model_path = st.text_input("Model path (.pt file)")
        tokenizer_path = st.text_input("Tokenizer path (directory)")

    if model_path and os.path.exists(str(model_path)):
        st.success(f"Model loaded: `{model_path}`")

        input_mode = st.radio("Input candidates", ["Paste text", "Upload file"], horizontal=True)

        candidates = []
        prompt_text = st.text_input("Prompt (optional context for scoring)", value="")

        if input_mode == "Paste text":
            raw = st.text_area(
                "Paste candidates (one JSON per line)",
                height=200,
                placeholder='{"weights": {"AAPL": 0.33, "GOOG": 0.33, "MSFT": 0.34}}\n{"weights": {"AAPL": 0.5, "GOOG": 0.5, "MSFT": 0.5}}',
            )
            if raw.strip():
                candidates = [line.strip() for line in raw.strip().splitlines() if line.strip()]
        else:
            cand_file = st.file_uploader("Upload candidates", type=["jsonl", "json", "csv"])
            if cand_file:
                from certainty.data.sampler import sampler_from_bytes
                candidates = sampler_from_bytes(cand_file.read(), cand_file.name)
                st.write(f"Loaded {len(candidates)} candidates")

        if candidates and st.button("Rerank Candidates", type="primary", key="rerank_btn"):
            with st.spinner("Scoring candidates..."):
                from certainty.inference.reranker import ConstraintReranker

                reranker = ConstraintReranker(
                    model_path=model_path,
                    tokenizer_path=tokenizer_path,
                )
                best, best_idx, energies = reranker.rerank(candidates, prompt_text)

            r1, r2 = st.columns(2)
            r1.metric("Best Candidate", f"#{best_idx + 1}")
            r2.metric("Best Energy", f"{energies[best_idx]:.4f}")

            energy_fn = st.session_state.get("energy_fn")
            if energy_fn:
                violations_before = 0
                for c in candidates:
                    try:
                        parsed = json.loads(c)
                        if energy_fn(parsed) > 0.01:
                            violations_before += 1
                    except Exception:
                        violations_before += 1

                baseline_rate = violations_before / len(candidates) * 100
                try:
                    best_parsed = json.loads(best)
                    best_energy = energy_fn(best_parsed)
                    after_rate = 100.0 if best_energy > 0.01 else 0.0
                except Exception:
                    after_rate = 100.0

                st.markdown("---")
                v1, v2, v3 = st.columns(3)
                v1.metric("Baseline Violation Rate", f"{baseline_rate:.1f}%")
                v2.metric("After Reranking", f"{after_rate:.1f}%", delta=f"-{baseline_rate - after_rate:.1f}%")
                v3.metric("Candidates Evaluated", len(candidates))

            import plotly.graph_objects as go

            sorted_indices = np.argsort(energies)
            colors = ["#00b894" if i == best_idx else "#636e72" for i in sorted_indices]

            fig = go.Figure(go.Bar(
                x=[f"#{i+1}" for i in sorted_indices],
                y=[energies[i] for i in sorted_indices],
                marker_color=colors,
                text=[f"{energies[i]:.3f}" for i in sorted_indices],
                textposition="outside",
            ))
            fig.update_layout(
                title="Candidate Energy Scores (lower = better)",
                xaxis_title="Candidate",
                yaxis_title="Energy",
                template="plotly_dark",
                height=350,
                margin=dict(t=40, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("**Best Candidate:**")
            st.code(best, language="json")

            with st.expander("All candidates with scores"):
                for i, (c, e) in enumerate(zip(candidates, energies)):
                    marker = " **(best)**" if i == best_idx else ""
                    st.markdown(f"**#{i+1}** | Energy: {e:.4f}{marker}")
                    st.code(c, language="json")

            results = {
                "best_index": best_idx,
                "best_candidate": best,
                "all_energies": energies,
                "candidates": candidates,
            }
            st.download_button(
                "Download results as JSON",
                data=json.dumps(results, indent=2, default=str),
                file_name="rerank_results.json",
                mime="application/json",
            )


# ── Sidebar ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### About")
    st.markdown(
        "**Certainty Labs** enforces hard constraints on LLM outputs "
        "using Energy-Based Models trained with the EORM architecture."
    )
    st.markdown("---")
    st.markdown("**Architecture:** TransEBM")
    st.markdown("**Loss:** Bradley-Terry (pairwise)")
    st.markdown("**Encoder:** From-scratch Transformer")
    st.markdown("**Tokenizer:** GPT-2")
    st.markdown("**Default Data:** GSM8K-Llama (EORM)")
    st.markdown("---")
    st.markdown(
        "**Research:**\n"
        "- [EORM (Jiang et al. 2025)](https://arxiv.org/abs/2505.14999)\n"
        "- [IRED (Du et al. 2024)](https://arxiv.org/abs/2406.11179)\n"
        "- [EBT (Gladstone et al. 2025)](https://energy-based-transformers.github.io)\n"
    )
    st.markdown("---")
    st.caption("v0.1.0 | MIT License")
