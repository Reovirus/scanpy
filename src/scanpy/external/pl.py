"""Plotting functions for external tools."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from anndata import AnnData  # noqa: TCH002
from matplotlib.axes import Axes  # noqa: TCH002
from sklearn.utils import deprecated

from .._compat import old_positionals
from .._utils import _doc_params
from .._utils._doctests import doctest_needs
from ..plotting import _scrublet, _utils, embedding
from ..plotting._docs import (
    doc_adata_color_etc,
    doc_edges_arrows,
    doc_scatter_embedding,
    doc_show_save_ax,
)
from ..plotting._tools.scatterplots import _wraps_plot_scatter
from .tl._wishbone import _anndata_to_wishbone

if TYPE_CHECKING:
    from collections.abc import Collection
    from typing import Any


__all__ = [
    "phate",
    "trimap",
    "harmony_timeseries",
    "sam",
    "wishbone_marker_trajectory",
]


@doctest_needs("phate")
@_wraps_plot_scatter
@_doc_params(
    adata_color_etc=doc_adata_color_etc,
    edges_arrows=doc_edges_arrows,
    scatter_bulk=doc_scatter_embedding,
    show_save_ax=doc_show_save_ax,
)
def phate(adata: AnnData, **kwargs) -> list[Axes] | None:
    """Scatter plot in PHATE basis.

    Parameters
    ----------
    {adata_color_etc}
    {edges_arrows}
    {scatter_bulk}
    {show_save_ax}

    Returns
    -------
    If `show==False`, a list of :class:`~matplotlib.axes.Axes` objects.
    Every second element corresponds to the 'right margin'
    drawing area for color bars and legends.

    Examples
    --------
    >>> from anndata import AnnData
    >>> import scanpy.external as sce
    >>> import phate
    >>> data, branches = phate.tree.gen_dla(
    ...     n_dim=100,
    ...     n_branch=20,
    ...     branch_length=100,
    ... )
    >>> data.shape
    (2000, 100)
    >>> adata = AnnData(data)
    >>> adata.obs["branches"] = branches
    >>> sce.tl.phate(adata, k=5, a=20, t=150)
    >>> adata.obsm["X_phate"].shape
    (2000, 2)
    >>> sce.pl.phate(
    ...     adata,
    ...     color="branches",
    ...     color_map="tab20",
    ... )

    """
    return embedding(adata, "phate", **kwargs)


@_wraps_plot_scatter
@_doc_params(
    adata_color_etc=doc_adata_color_etc,
    edges_arrows=doc_edges_arrows,
    scatter_bulk=doc_scatter_embedding,
    show_save_ax=doc_show_save_ax,
)
def trimap(adata: AnnData, **kwargs) -> Axes | list[Axes] | None:
    """Scatter plot in TriMap basis.

    Parameters
    ----------
    {adata_color_etc}
    {edges_arrows}
    {scatter_bulk}
    {show_save_ax}

    Returns
    -------
    If `show==False` a :class:`~matplotlib.axes.Axes` or a list of it.

    """
    return embedding(adata, "trimap", **kwargs)


@_wraps_plot_scatter
@_doc_params(
    adata_color_etc=doc_adata_color_etc,
    edges_arrows=doc_edges_arrows,
    scatter_bulk=doc_scatter_embedding,
    show_save_ax=doc_show_save_ax,
)
def harmony_timeseries(
    adata: AnnData, *, show: bool = True, return_fig: bool = False, **kwargs
) -> Axes | list[Axes] | None:
    """Scatter plot in Harmony force-directed layout basis.

    Parameters
    ----------
    {adata_color_etc}
    {edges_arrows}
    {scatter_bulk}
    {show_save_ax}

    Returns
    -------
    If `return_fig` is True, a :class:`~matplotlib.figure.Figure`.
    If `show==False` a :class:`~matplotlib.axes.Axes` or a list of it.

    """
    tp_name = adata.uns["harmony_timepoint_var"]
    tps = adata.obs[tp_name].unique()

    fig, axes = plt.subplots(1, len(tps))
    for i, tp in enumerate(tps):
        p = embedding(
            adata,
            "harmony",
            color=tp_name,
            groups=tp,
            title=tp,
            show=False,
            ax=axes[i],
            legend_loc="none",
        )
        p.set_axis_off()
    if return_fig:
        return fig
    if show:
        return None
    return axes


@old_positionals("c", "cmap", "linewidth", "edgecolor", "axes", "colorbar", "s")
def sam(
    adata: AnnData,
    projection: str | np.ndarray = "X_umap",
    *,
    c: str | np.ndarray | None = None,
    cmap: str = "Spectral_r",
    linewidth: float = 0.0,
    edgecolor: str = "k",
    axes: Axes | None = None,
    colorbar: bool = True,
    s: float = 10.0,
    **kwargs: Any,
) -> Axes:
    """Scatter plot using the SAM projection or another input projection.

    Parameters
    ----------
    projection
        A case-sensitive string indicating the projection to display (a key
        in adata.obsm) or a 2D numpy array with cell coordinates. If None,
        projection defaults to UMAP.
    c
        Cell color values overlaid on the projection. Can be a string from adata.obs
        to overlay cluster assignments / annotations or a 1D numpy array.
    axes
        Plot output to the specified, existing axes. If None, create new
        figure window.
    kwargs
        all keyword arguments in matplotlib.pyplot.scatter are eligible.

    """
    if isinstance(projection, str):
        try:
            dt = adata.obsm[projection]
        except KeyError as e:
            msg = "Please create a projection first using run_umap or run_tsne"
            raise ValueError(msg) from e
    else:
        dt = projection

    if axes is None:
        plt.figure()
        axes = plt.gca()

    if c is None:
        axes.scatter(
            dt[:, 0], dt[:, 1], s=s, linewidth=linewidth, edgecolor=edgecolor, **kwargs
        )
        return axes

    if isinstance(c, str):
        with contextlib.suppress(KeyError):
            c = np.array(list(adata.obs[c]))

    if isinstance(c[0], str | np.str_) and isinstance(c, np.ndarray | list):
        import samalg.utilities as ut

        i = ut.convert_annotations(c)
        ui, ai = np.unique(i, return_index=True)
        cax = axes.scatter(
            dt[:, 0],
            dt[:, 1],
            c=i,
            cmap=cmap,
            s=s,
            linewidth=linewidth,
            edgecolor=edgecolor,
            **kwargs,
        )

        if colorbar:
            cbar = plt.colorbar(cax, ax=axes, ticks=ui)
            cbar.ax.set_yticklabels(c[ai])
    else:
        if not isinstance(c, np.ndarray | list):
            colorbar = False
        i = c

        cax = axes.scatter(
            dt[:, 0],
            dt[:, 1],
            c=i,
            cmap=cmap,
            s=s,
            linewidth=linewidth,
            edgecolor=edgecolor,
            **kwargs,
        )

        if colorbar:
            plt.colorbar(cax, ax=axes)
    return axes


@old_positionals(
    "no_bins",
    "smoothing_factor",
    "min_delta",
    "show_variance",
    "figsize",
    "return_fig",
    "show",
    "save",
    "ax",
)
@_doc_params(show_save_ax=doc_show_save_ax)
def wishbone_marker_trajectory(
    adata: AnnData,
    markers: Collection[str],
    *,
    no_bins: int = 150,
    smoothing_factor: int = 1,
    min_delta: float = 0.1,
    show_variance: bool = False,
    figsize: tuple[float, float] | None = None,
    return_fig: bool = False,
    show: bool = True,
    save: str | bool | None = None,
    ax: Axes | None = None,
):
    """Plot marker trends along trajectory, and return trajectory branches.

    Intended for further analysis and visualization (heatmap, etc.).

    Parameters
    ----------
    adata
        Annotated data matrix.
    markers
        Iterable of markers/genes to be plotted.
    show_variance
        Logical indicating if the trends should be accompanied with variance.
    no_bins
        Number of bins for calculating marker density.
    smoothing_factor
        Parameter controlling the degree of smoothing.
    min_delta
        Minimum difference in marker expression after normalization to show
        separate trends for the two branches.
    figsize
        width, height
    return_fig
        Return the matplotlib figure.
    {show_save_ax}

    Returns
    -------
    Updates `adata` with the following fields:

    `trunk_wishbone` : :class:`pandas.DataFrame` (`adata.uns`)
        Computed values before branching
    `branch1_wishbone` : :class:`pandas.DataFrame` (`adata.uns`)
        Computed values for the first branch
    `branch2_wishbone` : :class:`pandas.DataFrame` (`adata.uns`)
        Computed values for the second branch.

    """
    wb = _anndata_to_wishbone(adata)

    if figsize is None:
        width = 2 * len(markers)
        height = 0.75 * len(markers)
    else:
        width, height = figsize

    if ax:
        fig = ax.figure
    else:
        fig = plt.figure(figsize=(width, height))
        ax = plt.gca()

    ret_values, fig, ax = wb.plot_marker_trajectory(
        markers=markers,
        show_variance=show_variance,
        no_bins=no_bins,
        smoothing_factor=smoothing_factor,
        min_delta=min_delta,
        fig=fig,
        ax=ax,
    )

    adata.uns["trunk_wishbone"] = ret_values["Trunk"]
    adata.uns["branch1_wishbone"] = ret_values["Branch1"]
    adata.uns["branch2_wishbone"] = ret_values["Branch2"]

    _utils.savefig_or_show("wishbone_trajectory", show=show, save=save)

    if return_fig:
        return fig
    if show:
        return None
    return ax


scrublet_score_distribution = deprecated("Import from sc.pl instead")(
    _scrublet.scrublet_score_distribution
)
