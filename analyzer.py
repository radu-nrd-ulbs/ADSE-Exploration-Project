import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class SimulationAnalyzer:
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
        self.data = []
        self.metrics_df = None
        self.power_data = []
        self.power_df = None
        
    def find_sim_files(self) -> List[Path]:
        sim_files = []
        
        sim_files.extend(self.workspace_path.glob("**/sim(*.out"))
        sim_files.extend(self.workspace_path.glob("**/sim.out"))
        sim_files.extend([f for f in self.workspace_path.glob("**/sim*.out") 
                          if f not in sim_files])
        
        return sorted(list(set(sim_files)))
    
    def find_powerstack_files(self) -> List[Path]:
        power_files = list(self.workspace_path.glob("**/powerstack*.txt"))
        return sorted(power_files)
    
    def extract_architecture_name(self, filename: str, parent_dir: str = "") -> str:
        match = re.search(r'sim\((.+?)\)\.out', filename)
        if match:
            return match.group(1)
            
        if parent_dir and parent_dir != '.':
            return parent_dir
        
        return filename.replace('.out', '').replace('sim', '').strip('()')
    
    def parse_sim_file(self, file_path: Path) -> Dict[str, float]:
        parent_dir = file_path.parent.name if file_path.parent != self.workspace_path else ""
        metrics = {'Architecture': self.extract_architecture_name(file_path.name, parent_dir),
                   'File Path': str(file_path.relative_to(self.workspace_path))}
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            cycles_match = re.search(r'Cycles\s*\|\s*(\d+)', content)
            if cycles_match:
                metrics['Cycles'] = int(cycles_match.group(1))
            
            ipc_match = re.search(r'IPC\s*\|\s*([\d.]+)', content)
            if ipc_match:
                metrics['IPC'] = float(ipc_match.group(1))
            
            l1d_match = re.search(
                r'Cache L1-D\s*\|.*?miss rate\s*\|\s*([\d.]+)%',
                content,
                re.DOTALL
            )
            if l1d_match:
                metrics['L1-D Miss Rate (%)'] = float(l1d_match.group(1))
            
            l2_match = re.search(
                r'Cache L2\s*\|.*?miss rate\s*\|\s*([\d.]+)%',
                content,
                re.DOTALL
            )
            if l2_match:
                metrics['L2 Miss Rate (%)'] = float(l2_match.group(1))
            
            l3_match = re.search(
                r'Cache L3\s*\|.*?miss rate\s*\|\s*([\d.]+)%',
                content,
                re.DOTALL
            )
            if l3_match:
                metrics['L3 Miss Rate (%)'] = float(l3_match.group(1))
            
            return metrics
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return metrics
    
    def parse_powerstack_file(self, file_path: Path) -> Dict[str, float]:
        parent_dir = file_path.parent.name if file_path.parent != self.workspace_path else ""
        arch_name = parent_dir if parent_dir else file_path.parent.name
        
        power_metrics = {
            'Architecture': arch_name if arch_name != '.' else 'default',
            'File Path': str(file_path.relative_to(self.workspace_path))
        }
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            total_power_match = re.search(r'total\s+([\d.]+)\s*W', content)
            if total_power_match:
                power_metrics['Total Power (W)'] = float(total_power_match.group(1))
            
            total_energy_match = re.search(r'total\s+[\d.]+\s*W\s+([\d.]+)\s*J', content)
            if total_energy_match:
                power_metrics['Total Energy (J)'] = float(total_energy_match.group(1))
            
            core_power_match = re.search(r'^\s*core\s+([\d.]+)\s*W', content, re.MULTILINE)
            if core_power_match:
                power_metrics['Core Power (W)'] = float(core_power_match.group(1))
            
            cache_power_match = re.search(r'^\s*cache\s+([\d.]+)\s*W', content, re.MULTILINE)
            if cache_power_match:
                power_metrics['Cache Power (W)'] = float(cache_power_match.group(1))
            
            dram_power_match = re.search(r'^\s*dram\s+([\d.]+)\s*W', content, re.MULTILINE)
            if dram_power_match:
                power_metrics['DRAM Power (W)'] = float(dram_power_match.group(1))
            
            return power_metrics
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return power_metrics
    
    def analyze_all(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        sim_files = self.find_sim_files()
        
        if not sim_files:
            print("No sim.out files found!")
        else:
            print(f"Found {len(sim_files)} simulation files")
            for sim_file in sim_files:
                print(f"Parsing {sim_file.relative_to(self.workspace_path)}...", end=" ")
                metrics = self.parse_sim_file(sim_file)
                self.data.append(metrics)
                print("✓")
            self.metrics_df = pd.DataFrame(self.data)

        power_files = self.find_powerstack_files()
        
        if not power_files:
            print("No powerstack.txt files found.")
        else:
            print(f"\nFound {len(power_files)} powerstack files")
            for power_file in power_files:
                print(f"Parsing {power_file.relative_to(self.workspace_path)}...", end=" ")
                power_metrics = self.parse_powerstack_file(power_file)
                self.power_data.append(power_metrics)
                print("✓")
            self.power_df = pd.DataFrame(self.power_data)
        
        return self.metrics_df, self.power_df
    
    def generate_summary_table(self) -> None:
        output_dir = self.workspace_path / "analysis_results"
        output_dir.mkdir(exist_ok=True)
        
        if self.metrics_df is not None and len(self.metrics_df) > 0:
            print("\n" + "="*80)
            print("SIMULATION METRICS SUMMARY")
            print("="*80)
            display_df = self.metrics_df.drop(columns=['File Path'], errors='ignore')
            print(display_df.to_string(index=False))
            print("="*80 + "\n")
            
            csv_path = output_dir / "metrics_summary.csv"
            self.metrics_df.to_csv(csv_path, index=False)
            print(f"Summary table saved to: {csv_path}")
            
            txt_path = output_dir / "metrics_summary.txt"
            with open(txt_path, 'w') as f:
                f.write("SIMULATION METRICS SUMMARY\n")
                f.write("="*80 + "\n")
                f.write(display_df.to_string(index=False))
                f.write("\n" + "="*80 + "\n")
            print(f"Summary table saved to: {txt_path}")
        
        if self.power_df is not None and len(self.power_df) > 0:
            print("\n" + "="*80)
            print("POWER METRICS SUMMARY")
            print("="*80)
            display_power_df = self.power_df.drop(columns=['File Path'], errors='ignore')
            print(display_power_df.to_string(index=False))
            print("="*80 + "\n")
            
            power_csv_path = output_dir / "power_summary.csv"
            self.power_df.to_csv(power_csv_path, index=False)
            print(f"Power summary saved to: {power_csv_path}")
            
            power_txt_path = output_dir / "power_summary.txt"
            with open(power_txt_path, 'w') as f:
                f.write("POWER METRICS SUMMARY\n")
                f.write("="*80 + "\n")
                f.write(display_power_df.to_string(index=False))
                f.write("\n" + "="*80 + "\n")
            print(f"Power summary saved to: {power_txt_path}")
    
    def plot_cycles_vs_architecture(self) -> None:
        if 'Cycles' not in self.metrics_df.columns:
            print("Cycles data not available")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        self.metrics_df.plot(
            x='Architecture',
            y='Cycles',
            kind='bar',
            ax=ax,
            color='steelblue',
            legend=False
        )
        
        ax.set_title('Cycles by Architecture', fontsize=14, fontweight='bold')
        ax.set_xlabel('Architecture', fontsize=12)
        ax.set_ylabel('Cycles', fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        output_path = self.workspace_path / "analysis_results" / "cycles_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()
    
    def plot_ipc_vs_architecture(self) -> None:
        if 'IPC' not in self.metrics_df.columns:
            print("IPC data not available")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        self.metrics_df.plot(
            x='Architecture',
            y='IPC',
            kind='bar',
            ax=ax,
            color='darkgreen',
            legend=False
        )
        
        ax.set_title('Instructions Per Cycle (IPC) by Architecture', fontsize=14, fontweight='bold')
        ax.set_xlabel('Architecture', fontsize=12)
        ax.set_ylabel('IPC', fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        output_path = self.workspace_path / "analysis_results" / "ipc_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()
    
    def plot_cache_miss_rates(self) -> None:
        cache_cols = ['L1-D Miss Rate (%)', 'L2 Miss Rate (%)', 'L3 Miss Rate (%)']
        available_cols = [col for col in cache_cols if col in self.metrics_df.columns]
        
        if not available_cols:
            print("Cache miss rate data not available")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(self.metrics_df))
        width = 0.25
        
        for i, col in enumerate(available_cols):
            offset = (i - len(available_cols)/2 + 0.5) * width
            ax.bar(
                [pos + offset for pos in x],
                self.metrics_df[col],
                width=width,
                label=col.replace(' (%)', ''),
                alpha=0.8
            )
        
        ax.set_title('Cache Miss Rates by Architecture', fontsize=14, fontweight='bold')
        ax.set_xlabel('Architecture', fontsize=12)
        ax.set_ylabel('Miss Rate (%)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(self.metrics_df['Architecture'], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        output_path = self.workspace_path / "analysis_results" / "cache_miss_rates.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()
    
    def plot_heatmap(self) -> None:
        if self.metrics_df is None or len(self.metrics_df) == 0:
            return
        
        numeric_df = self.metrics_df.select_dtypes(include=['number']).copy()
        
        if numeric_df.empty:
            print("No numeric data for heatmap")
            return
        
        normalized_df = (numeric_df - numeric_df.min()) / (numeric_df.max() - numeric_df.min())
        normalized_df.index = self.metrics_df['Architecture']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sns.heatmap(
            normalized_df.T,
            annot=True,
            fmt='.2f',
            cmap='RdYlGn_r',
            ax=ax,
            cbar_kws={'label': 'Normalized Value'}
        )
        
        ax.set_title('Normalized Metrics Heatmap (All Architectures)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Architecture', fontsize=12)
        ax.set_ylabel('Metric', fontsize=12)
        plt.tight_layout()
        
        output_path = self.workspace_path / "analysis_results" / "metrics_heatmap.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()
    
    def plot_power_metrics(self) -> None:
        if self.power_df is None or len(self.power_df) == 0:
            return
        
        output_dir = self.workspace_path / "analysis_results"
        
        if 'Total Power (W)' in self.power_df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            self.power_df.plot(
                x='Architecture',
                y='Total Power (W)',
                kind='bar',
                ax=ax,
                color='orange',
                legend=False
            )
            ax.set_title('Total Power Consumption by Architecture', fontsize=14, fontweight='bold')
            ax.set_xlabel('Architecture', fontsize=12)
            ax.set_ylabel('Power (W)', fontsize=12)
            ax.grid(axis='y', alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            output_path = output_dir / "power_total.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {output_path}")
            plt.close()
        
        power_cols = ['Core Power (W)', 'Cache Power (W)', 'DRAM Power (W)']
        available_power_cols = [col for col in power_cols if col in self.power_df.columns]
        
        if available_power_cols:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            x = range(len(self.power_df))
            width = 0.25
            
            for i, col in enumerate(available_power_cols):
                offset = (i - len(available_power_cols)/2 + 0.5) * width
                ax.bar(
                    [pos + offset for pos in x],
                    self.power_df[col],
                    width=width,
                    label=col.replace(' (W)', ''),
                    alpha=0.8
                )
            
            ax.set_title('Power Breakdown by Component', fontsize=14, fontweight='bold')
            ax.set_xlabel('Architecture', fontsize=12)
            ax.set_ylabel('Power (W)', fontsize=12)
            ax.set_xticks(x)
            ax.set_xticklabels(self.power_df['Architecture'], rotation=45, ha='right')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            
            output_path = output_dir / "power_breakdown.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {output_path}")
            plt.close()

        if 'Total Energy (mJ)' in self.power_df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            self.power_df.plot(
                x='Architecture',
                y='Total Energy (mJ)',
                kind='bar',
                ax=ax,
                color='red',
                legend=False
            )
            ax.set_title('Total Energy Consumption by Architecture', fontsize=14, fontweight='bold')
            ax.set_xlabel('Architecture', fontsize=12)
            ax.set_ylabel('Energy (mJ)', fontsize=12)
            ax.grid(axis='y', alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            output_path = output_dir / "energy_total.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {output_path}")
            plt.close()
    
    def generate_all_visualizations(self) -> None:
        output_dir = self.workspace_path / "analysis_results"
        output_dir.mkdir(exist_ok=True)
        
        print("\nGenerating visualizations...")
        print("-" * 40)
        
        self.generate_summary_table()
        
        if self.metrics_df is not None and len(self.metrics_df) > 0:
            self.plot_cycles_vs_architecture()
            self.plot_ipc_vs_architecture()
            self.plot_cache_miss_rates()
            self.plot_heatmap()
        
        if self.power_df is not None and len(self.power_df) > 0:
            self.plot_power_metrics()
        
        print("-" * 40)
        print(f"\nAll results saved to: {output_dir}\n")
    
    def get_statistics(self) -> None:
        if self.metrics_df is not None and len(self.metrics_df) > 0:
            print("\n" + "="*80)
            print("SIMULATION METRICS - STATISTICAL SUMMARY")
            print("="*80)
            
            numeric_df = self.metrics_df.select_dtypes(include=['number'])
            if not numeric_df.empty:
                print(numeric_df.describe().to_string())
            print("="*80 + "\n")
        
        if self.power_df is not None and len(self.power_df) > 0:
            print("\n" + "="*80)
            print("POWER METRICS - STATISTICAL SUMMARY")
            print("="*80)
            
            numeric_power_df = self.power_df.select_dtypes(include=['number'])
            if not numeric_power_df.empty:
                print(numeric_power_df.describe().to_string())
            print("="*80 + "\n")


def analyse_results(workspace_path:str):
    print("="*80)
    print("SIMULATION ANALYZER")
    print("="*80)
    
    analyzer = SimulationAnalyzer(workspace_path)
    analyzer.analyze_all()
    
    if (analyzer.metrics_df is not None and len(analyzer.metrics_df) > 0) or \
       (analyzer.power_df is not None and len(analyzer.power_df) > 0):
        analyzer.generate_all_visualizations()
        analyzer.get_statistics()
        
        print("Analysis complete! Check 'analysis_results' folder for outputs.")
    else:
        print("No simulation or power data found to analyze.")
