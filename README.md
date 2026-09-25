# Argumentation Framework Subsampling and Analysis

Research tools for **subsampling abstract argumentation frameworks** and analyzing the resulting graphs.

## Repository guide

- [subsampling_lib.py](subsampling_lib.py): subsampling implementation.
- [af_subsample.py](af_subsample.py) and [sample_afs.py](sample_afs.py): sampling entry points.
- [calculate_metrics.py](calculate_metrics.py) and [analysis.py](analysis.py): graph metrics and analysis.
- [solve_grounded.py](solve_grounded.py): grounded-semantics solving.
- [tgf_to_iccma23.py](tgf_to_iccma23.py): format conversion.

Start by inspecting the sampling scripts and selecting the input frameworks and output paths for your experiment. The scripts form a research workflow rather than an installed command-line package.

For related framework data and graph-learning code, see [AFGraphLib](https://github.com/lmlearning/AFGraphLib).

## License

See [LICENSE](LICENSE).
