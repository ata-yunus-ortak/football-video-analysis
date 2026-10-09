# Attribution and third-party notices

The new code is MIT-licensed. That permission does not grant rights to dependencies, tutorial materials, user-supplied footage, datasets or trained models.

- **Abdullah Tarek / codeinajiffy**: [tutorial project](https://github.com/abdullahtarek/football_analysis), [YouTube channel](https://www.youtube.com/@codeinajiffy). Credited for the football-analysis learning workflow. No tutorial files are redistributed.
- **Ultralytics YOLO**: optional inference only. The provider describes AGPL-3.0 and Enterprise licensing at its [official licensing page](https://www.ultralytics.com/license). The repository's MIT license does not override obligations for an application combined with Ultralytics or a model. Weights are supplied by the user and may carry additional conditions. [Prediction documentation](https://docs.ultralytics.com/modes/predict/).
- **Supervision / ByteTrack integration**: optional inference dependency. See its [repository and license](https://github.com/roboflow/supervision) and [tracker documentation](https://supervision.roboflow.com/latest/trackers/). It is not an algorithm invented in this portfolio.
- **PyTorch / TorchVision**, **OpenCV**, and **NumPy**: optional runtimes. See [PyTorch](https://github.com/pytorch/pytorch/blob/main/LICENSE), [TorchVision](https://github.com/pytorch/vision/blob/main/LICENSE), [OpenCV](https://github.com/opencv/opencv/blob/4.x/LICENSE), and [NumPy](https://github.com/numpy/numpy/blob/main/LICENSE.txt) for upstream terms.

Dependencies are installed separately and not vendored. Consult the license of the exact installed version and the source/model/data combination you distribute. The offline path uses only Python's standard library and does not import the optional inference stack.
