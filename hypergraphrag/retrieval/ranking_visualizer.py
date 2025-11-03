"""
Ranking Visualization Module

This module provides visualization tools for quality-aware ranking results,
helping users understand how different factors contribute to the final ranking.

Key Features:
- Component contribution bar charts
- Score distribution histograms
- Ranking comparison plots
- Factor importance visualization

Usage:
    from hypergraphrag.retrieval.ranking_visualizer import RankingVisualizer
    
    visualizer = RankingVisualizer()
    visualizer.plot_ranking_components(ranked_results)
    visualizer.save_visualization("ranking_analysis.png")
"""

import logging
from typing import List, Dict, Optional, Tuple
import json

logger = logging.getLogger(__name__)

# Optional matplotlib import
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning(
        "matplotlib not available. Install with: pip install matplotlib"
    )

# Optional numpy import
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning(
        "numpy not available. Install with: pip install numpy"
    )


class RankingVisualizer:
    """
    Visualizer for quality-aware ranking results.
    
    This class provides various visualization methods to help understand
    how similarity, quality, and dynamic weights contribute to final rankings.
    
    Attributes:
        figsize: Default figure size for plots (width, height)
        dpi: Resolution for saved figures
        style: Matplotlib style to use
    """
    
    def __init__(
        self,
        figsize: Tuple[int, int] = (12, 8),
        dpi: int = 100,
        style: str = "seaborn-v0_8-darkgrid"
    ):
        """
        Initialize RankingVisualizer.
        
        Args:
            figsize: Default figure size (width, height) in inches
            dpi: Resolution for saved figures
            style: Matplotlib style (e.g., 'seaborn', 'ggplot', 'default')
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError(
                "matplotlib is required for visualization. "
                "Install with: pip install matplotlib"
            )
        
        self.figsize = figsize
        self.dpi = dpi
        self.style = style
        self.current_figure = None
        
        # Try to set style, fall back to default if not available
        try:
            plt.style.use(style)
        except:
            logger.warning(f"Style '{style}' not available, using default")
            plt.style.use("default")
        
        logger.info(f"RankingVisualizer initialized with figsize={figsize}, dpi={dpi}")
    
    def plot_ranking_components(
        self,
        ranked_results: List[Dict],
        top_k: int = 10,
        title: Optional[str] = None
    ) -> Figure:
        """
        Plot stacked bar chart showing component contributions for top-k results.
        
        This visualization shows how similarity, quality, and dynamic weight
        contribute to the final score for each hyperedge.
        
        Args:
            ranked_results: List of ranked hyperedge dicts with ranking_components
            top_k: Number of top results to visualize
            title: Custom title for the plot
            
        Returns:
            matplotlib Figure object
            
        Example:
            >>> visualizer = RankingVisualizer()
            >>> fig = visualizer.plot_ranking_components(ranked_results, top_k=5)
            >>> plt.show()
        """
        if not ranked_results:
            logger.warning("No results to visualize")
            return None
        
        # Check if ranking_components are available
        if "ranking_components" not in ranked_results[0]:
            logger.error(
                "ranking_components not found. "
                "Enable explanations in QualityAwareRanker with provide_explanation=True"
            )
            return None
        
        # Extract top-k results
        top_results = ranked_results[:min(top_k, len(ranked_results))]
        
        # Extract data
        labels = []
        similarity_scores = []
        quality_scores = []
        dynamic_scores = []
        
        for i, he in enumerate(top_results):
            components = he["ranking_components"]
            weights = components["weights"]
            
            # Get weighted contributions
            sim_contrib = components["similarity"] * weights["alpha"]
            qual_contrib = components["quality"] * weights["beta"]
            dyn_contrib = components["dynamic_weight"] * weights["gamma"]
            
            labels.append(f"#{i+1}")
            similarity_scores.append(sim_contrib)
            quality_scores.append(qual_contrib)
            dynamic_scores.append(dyn_contrib)
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        # Create stacked bar chart
        x = range(len(labels))
        width = 0.6
        
        p1 = ax.bar(x, similarity_scores, width, label='Similarity', color='#3498db')
        p2 = ax.bar(x, quality_scores, width, bottom=similarity_scores,
                    label='Quality', color='#2ecc71')
        
        bottom = [s + q for s, q in zip(similarity_scores, quality_scores)]
        p3 = ax.bar(x, dynamic_scores, width, bottom=bottom,
                    label='Dynamic Weight', color='#e74c3c')
        
        # Customize plot
        ax.set_xlabel('Ranking Position', fontsize=12, fontweight='bold')
        ax.set_ylabel('Score Contribution', fontsize=12, fontweight='bold')
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        else:
            ax.set_title(
                f'Ranking Component Contributions (Top {len(top_results)})',
                fontsize=14,
                fontweight='bold'
            )
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        # Add final score labels on top of bars
        for i, (s, q, d) in enumerate(zip(similarity_scores, quality_scores, dynamic_scores)):
            total = s + q + d
            ax.text(i, total + 0.02, f'{total:.3f}', ha='center', va='bottom',
                   fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        self.current_figure = fig
        
        logger.info(f"Generated ranking components plot for top {len(top_results)} results")
        return fig
    
    def plot_score_distribution(
        self,
        ranked_results: List[Dict],
        bins: int = 20,
        title: Optional[str] = None
    ) -> Figure:
        """
        Plot histogram of final scores distribution.
        
        Args:
            ranked_results: List of ranked hyperedge dicts
            bins: Number of histogram bins
            title: Custom title for the plot
            
        Returns:
            matplotlib Figure object
        """
        if not ranked_results:
            logger.warning("No results to visualize")
            return None
        
        # Extract final scores
        scores = [he["final_score"] for he in ranked_results]
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        # Plot histogram
        n, bins_edges, patches = ax.hist(
            scores,
            bins=bins,
            color='#3498db',
            alpha=0.7,
            edgecolor='black'
        )
        
        # Add mean and median lines
        mean_score = np.mean(scores) if NUMPY_AVAILABLE else sum(scores) / len(scores)
        median_score = np.median(scores) if NUMPY_AVAILABLE else sorted(scores)[len(scores)//2]
        
        ax.axvline(mean_score, color='red', linestyle='--', linewidth=2,
                  label=f'Mean: {mean_score:.3f}')
        ax.axvline(median_score, color='green', linestyle='--', linewidth=2,
                  label=f'Median: {median_score:.3f}')
        
        # Customize plot
        ax.set_xlabel('Final Score', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        else:
            ax.set_title(
                f'Score Distribution ({len(ranked_results)} hyperedges)',
                fontsize=14,
                fontweight='bold'
            )
        
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        self.current_figure = fig
        
        logger.info(f"Generated score distribution plot for {len(ranked_results)} results")
        return fig
    
    def plot_factor_comparison(
        self,
        ranked_results: List[Dict],
        top_k: int = 10,
        title: Optional[str] = None
    ) -> Figure:
        """
        Plot grouped bar chart comparing raw factor values.
        
        This shows the raw similarity, quality, and dynamic weight values
        (before weighting) for each hyperedge.
        
        Args:
            ranked_results: List of ranked hyperedge dicts with ranking_components
            top_k: Number of top results to visualize
            title: Custom title for the plot
            
        Returns:
            matplotlib Figure object
        """
        if not ranked_results:
            logger.warning("No results to visualize")
            return None
        
        if "ranking_components" not in ranked_results[0]:
            logger.error("ranking_components not found")
            return None
        
        # Extract top-k results
        top_results = ranked_results[:min(top_k, len(ranked_results))]
        
        # Extract data
        labels = [f"#{i+1}" for i in range(len(top_results))]
        similarity = [he["ranking_components"]["similarity"] for he in top_results]
        quality = [he["ranking_components"]["quality"] for he in top_results]
        dynamic = [he["ranking_components"]["dynamic_weight"] for he in top_results]
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        # Set up grouped bars
        x = np.arange(len(labels)) if NUMPY_AVAILABLE else list(range(len(labels)))
        width = 0.25
        
        ax.bar([i - width for i in x], similarity, width, label='Similarity',
               color='#3498db', alpha=0.8)
        ax.bar(x, quality, width, label='Quality',
               color='#2ecc71', alpha=0.8)
        ax.bar([i + width for i in x], dynamic, width, label='Dynamic Weight',
               color='#e74c3c', alpha=0.8)
        
        # Customize plot
        ax.set_xlabel('Ranking Position', fontsize=12, fontweight='bold')
        ax.set_ylabel('Factor Value', fontsize=12, fontweight='bold')
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        else:
            ax.set_title(
                f'Factor Comparison (Top {len(top_results)})',
                fontsize=14,
                fontweight='bold'
            )
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, 1.1)
        
        plt.tight_layout()
        self.current_figure = fig
        
        logger.info(f"Generated factor comparison plot for top {len(top_results)} results")
        return fig
    
    def plot_weight_impact(
        self,
        ranked_results: List[Dict],
        top_k: int = 5,
        title: Optional[str] = None
    ) -> Figure:
        """
        Plot pie charts showing weight impact for top results.
        
        Args:
            ranked_results: List of ranked hyperedge dicts with ranking_components
            top_k: Number of top results to visualize
            title: Custom title for the plot
            
        Returns:
            matplotlib Figure object
        """
        if not ranked_results:
            logger.warning("No results to visualize")
            return None
        
        if "ranking_components" not in ranked_results[0]:
            logger.error("ranking_components not found")
            return None
        
        # Extract top-k results
        top_results = ranked_results[:min(top_k, len(ranked_results))]
        
        # Create subplots
        n_cols = min(3, len(top_results))
        n_rows = (len(top_results) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4, n_rows * 4), dpi=self.dpi)
        
        if len(top_results) == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if n_rows > 1 else axes
        
        colors = ['#3498db', '#2ecc71', '#e74c3c']
        
        for i, he in enumerate(top_results):
            components = he["ranking_components"]
            weights = components["weights"]
            
            # Calculate contributions
            sim_contrib = components["similarity"] * weights["alpha"]
            qual_contrib = components["quality"] * weights["beta"]
            dyn_contrib = components["dynamic_weight"] * weights["gamma"]
            
            values = [sim_contrib, qual_contrib, dyn_contrib]
            labels = ['Similarity', 'Quality', 'Dynamic']
            
            # Plot pie chart
            axes[i].pie(values, labels=labels, colors=colors, autopct='%1.1f%%',
                       startangle=90)
            axes[i].set_title(f'Rank #{i+1}\nScore: {he["final_score"]:.3f}',
                            fontsize=10, fontweight='bold')
        
        # Hide unused subplots
        for i in range(len(top_results), len(axes)):
            axes[i].axis('off')
        
        if title:
            fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
        else:
            fig.suptitle(
                f'Weight Impact Analysis (Top {len(top_results)})',
                fontsize=14,
                fontweight='bold',
                y=0.98
            )
        
        plt.tight_layout()
        self.current_figure = fig
        
        logger.info(f"Generated weight impact plot for top {len(top_results)} results")
        return fig
    
    def save_visualization(self, filepath: str, dpi: Optional[int] = None):
        """
        Save the current figure to file.
        
        Args:
            filepath: Output file path (e.g., 'ranking.png', 'analysis.pdf')
            dpi: Resolution (uses default if not specified)
        """
        if self.current_figure is None:
            logger.error("No figure to save. Generate a plot first.")
            return
        
        dpi = dpi or self.dpi
        self.current_figure.savefig(filepath, dpi=dpi, bbox_inches='tight')
        logger.info(f"Visualization saved to {filepath}")
    
    def generate_text_report(
        self,
        ranked_results: List[Dict],
        top_k: int = 10
    ) -> str:
        """
        Generate a text-based ranking report.
        
        Args:
            ranked_results: List of ranked hyperedge dicts
            top_k: Number of top results to include
            
        Returns:
            Formatted text report
        """
        if not ranked_results:
            return "No results to report"
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("RANKING ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Summary statistics
        scores = [he["final_score"] for he in ranked_results]
        mean_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        report_lines.append(f"Total Results: {len(ranked_results)}")
        report_lines.append(f"Score Range: [{min_score:.3f}, {max_score:.3f}]")
        report_lines.append(f"Mean Score: {mean_score:.3f}")
        report_lines.append("")
        
        # Top-k results
        report_lines.append(f"TOP {min(top_k, len(ranked_results))} RESULTS:")
        report_lines.append("-" * 80)
        
        for i, he in enumerate(ranked_results[:top_k], 1):
            report_lines.append(f"\n#{i} - Final Score: {he['final_score']:.3f}")
            
            if "ranking_components" in he:
                components = he["ranking_components"]
                report_lines.append(f"  Similarity: {components['similarity']:.3f}")
                report_lines.append(f"  Quality: {components['quality']:.3f}")
                report_lines.append(f"  Dynamic Weight: {components['dynamic_weight']:.3f}")
                report_lines.append(f"  Computation: {components['computation']}")
            
            # Show hyperedge content (truncated)
            if "hyperedge" in he:
                content = he["hyperedge"]
                if len(content) > 100:
                    content = content[:97] + "..."
                report_lines.append(f"  Content: {content}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def export_ranking_data(
        self,
        ranked_results: List[Dict],
        filepath: str,
        format: str = "json"
    ):
        """
        Export ranking data to file.
        
        Args:
            ranked_results: List of ranked hyperedge dicts
            filepath: Output file path
            format: Export format ('json' or 'csv')
        """
        if format == "json":
            # Export as JSON
            export_data = []
            for i, he in enumerate(ranked_results, 1):
                entry = {
                    "rank": i,
                    "final_score": he.get("final_score", 0),
                    "hyperedge_name": he.get("hyperedge_name", ""),
                    "hyperedge": he.get("hyperedge", "")
                }
                
                if "ranking_components" in he:
                    entry["components"] = he["ranking_components"]
                
                export_data.append(entry)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Ranking data exported to {filepath} (JSON)")
        
        elif format == "csv":
            # Export as CSV
            import csv
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    "Rank", "Final Score", "Similarity", "Quality",
                    "Dynamic Weight", "Hyperedge Name"
                ])
                
                # Data
                for i, he in enumerate(ranked_results, 1):
                    row = [
                        i,
                        f"{he.get('final_score', 0):.3f}"
                    ]
                    
                    if "ranking_components" in he:
                        comp = he["ranking_components"]
                        row.extend([
                            f"{comp['similarity']:.3f}",
                            f"{comp['quality']:.3f}",
                            f"{comp['dynamic_weight']:.3f}"
                        ])
                    else:
                        row.extend(["N/A", "N/A", "N/A"])
                    
                    row.append(he.get("hyperedge_name", ""))
                    writer.writerow(row)
            
            logger.info(f"Ranking data exported to {filepath} (CSV)")
        
        else:
            logger.error(f"Unsupported export format: {format}")


def create_ranking_dashboard(
    ranked_results: List[Dict],
    output_path: str = "ranking_dashboard.png",
    top_k: int = 10
):
    """
    Create a comprehensive dashboard with multiple visualizations.
    
    Args:
        ranked_results: List of ranked hyperedge dicts
        output_path: Output file path
        top_k: Number of top results to visualize
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("matplotlib required for dashboard")
        return
    
    visualizer = RankingVisualizer(figsize=(16, 12))
    
    # Create 2x2 subplot layout
    fig = plt.figure(figsize=(16, 12), dpi=100)
    
    # Plot 1: Component contributions
    plt.subplot(2, 2, 1)
    visualizer.plot_ranking_components(ranked_results, top_k=top_k)
    
    # Plot 2: Score distribution
    plt.subplot(2, 2, 2)
    visualizer.plot_score_distribution(ranked_results)
    
    # Plot 3: Factor comparison
    plt.subplot(2, 2, 3)
    visualizer.plot_factor_comparison(ranked_results, top_k=top_k)
    
    # Plot 4: Weight impact (just top 3)
    plt.subplot(2, 2, 4)
    visualizer.plot_weight_impact(ranked_results, top_k=3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Ranking dashboard saved to {output_path}")
