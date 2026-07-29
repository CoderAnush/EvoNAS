# Research Datasets

| Dataset | Role | Config |
|---|---|---|
| Toy Quick | CI / demo / unit drift | `configs/datasets/toy_quick.yaml` |
| MNIST | Classic vision baseline | `configs/datasets/mnist.yaml` |
| Fashion-MNIST | Slightly harder vision | `configs/datasets/fashion_mnist.yaml` |
| CIFAR-10 | Research stretch | `configs/datasets/cifar10.yaml` |

## Notes

- Phase 1 supports synthetic placeholders; torchvision optional.  
- Continuous learning stream simulation uses index windows over static splits.  
- Paper should state which loader backend and subset fractions were used.
