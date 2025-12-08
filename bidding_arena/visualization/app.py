import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from typing import List, Dict

from bidding_arena.core.constants import StrategyType
from bidding_arena.core.strategy import DynamicStrategy
from bidding_arena.core.engine import ReplayEngine
from bidding_arena.generation.generator import StrategyGenerator
from bidding_arena.generation.llm_client import MockLLMClient, OllamaLLMClient
from bidding_arena.data.generator import MockDataGenerator

def main():
    st.set_page_config(page_title="Bidding Strategy Arena", layout="wide")
    st.title("🤖 LLM Bidding Strategy Arena")

    # Sidebar: Configuration
    st.sidebar.header("Configuration")
    
    use_ollama = st.sidebar.checkbox("Use Real Ollama (Gemma3)", value=False)
    model_name = st.sidebar.text_input("Model Name", value="gemma3:12b") if use_ollama else "mock"
    
    selected_types = st.sidebar.multiselect(
        "Select Strategy Types to Generate",
        [t.value for t in StrategyType],
        default=[StrategyType.IMPRESSION_FOCUSED.value, StrategyType.AGGRESSIVE.value]
    )

    initial_budget = st.sidebar.number_input("Initial Budget ($)", value=100.0)
    num_records = st.sidebar.slider("Simulation Records", 100, 5000, 1000)

    if st.sidebar.button("🚀 Generate & Compete"):
        run_arena(use_ollama, model_name, selected_types, initial_budget, num_records)

def run_arena(use_ollama, model_name, selected_types, initial_budget, num_records):
    # 1. Setup Clients
    if use_ollama:
        try:
            llm_client = OllamaLLMClient(model=model_name)
        except Exception as e:
            st.error(f"Failed to initialize Ollama: {e}")
            return
    else:
        llm_client = MockLLMClient()
    
    generator = StrategyGenerator(llm_client)
    
    # 2. Data Generation
    with st.spinner("Generating Market Data..."):
        data_gen = MockDataGenerator()
        market_data = data_gen.generate_data(num_records)
        st.success(f"Generated {len(market_data)} bid requests.")
        
        # Show data sample
        with st.expander("View Market Data Sample"):
            st.dataframe(market_data.head())

    # 3. Strategy Generation & Execution
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, s_type_str in enumerate(selected_types):
        s_type = StrategyType(s_type_str)
        status_text.text(f"Generating strategy for {s_type.value}...")
        
        try:
            # Generate Code
            metadata = generator.generate(s_type)
            strategy = DynamicStrategy(metadata)
            
            # Show Code
            with st.expander(f"📜 Strategy Code: {s_type.value}"):
                st.code(metadata.code, language="python")
            
            # Run Simulation
            engine = ReplayEngine(initial_budget=initial_budget)
            sim_result = engine.run(strategy, market_data)
            
            sim_result['strategy_name'] = s_type.value
            results.append(sim_result)
            
        except Exception as e:
            st.error(f"Error processing {s_type.value}: {e}")
        
        progress_bar.progress((i + 1) / len(selected_types))

    status_text.text("Competition finished!")
    
    if not results:
        return

    # 4. Visualization
    st.divider()
    st.subheader("🏆 Competition Results")

    # Metrics Table
    metrics_df = pd.DataFrame([{
        "Strategy": r['strategy_name'],
        "Wins": r['win_count'],
        "Win Rate": f"{r['win_rate']:.2%}",
        "Spend": f"${r['total_spend']:.2f}",
        "Conversions": r['conversion_count'],
        "CPA": f"${r['avg_cpa']:.2f}",
        "ROI": f"{r['roi']:.2f}"
    } for r in results])
    
    st.table(metrics_df)

    # Charts
    col1, col2 = st.columns(2)
    
    # Prepare Time Series Data
    all_history = []
    for r in results:
        hist_df = pd.DataFrame(r['history'])
        hist_df['Strategy'] = r['strategy_name']
        all_history.append(hist_df)
    
    if all_history:
        full_hist = pd.concat(all_history)
        
        with col1:
            st.markdown("### 📉 Remaining Budget vs Time")
            fig_budget = px.line(full_hist, x="timestamp", y="remaining_budget", color="Strategy", markers=True)
            st.plotly_chart(fig_budget, use_container_width=True)
            
        with col2:
            st.markdown("### 💰 Cumulative Spend vs Time")
            fig_spend = px.line(full_hist, x="timestamp", y="total_spend", color="Strategy", markers=True)
            st.plotly_chart(fig_spend, use_container_width=True)
            
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("### 🎯 Cumulative Conversions")
            fig_conv = px.line(full_hist, x="timestamp", y="conversion_count", color="Strategy", markers=True)
            st.plotly_chart(fig_conv, use_container_width=True)

        with col4:
            st.markdown("### 📊 Win Rate & Conversion Efficiency")
            # Bar chart for final metrics
            fig_bar = go.Figure(data=[
                go.Bar(name='Win Rate', x=metrics_df['Strategy'], y=[float(x.strip('%'))/100 for x in metrics_df['Win Rate']]),
                go.Bar(name='ROI', x=metrics_df['Strategy'], y=[float(x) for x in metrics_df['ROI']])
            ])
            fig_bar.update_layout(barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)

if __name__ == "__main__":
    main()

