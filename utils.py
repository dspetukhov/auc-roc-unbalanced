# import random
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.metrics import roc_curve, precision_recall_curve
import matplotlib.pyplot as plt

seeds = [978, 672, 821, 445, 488, 449, 753, 962, 874, 287, 257, 598, 100, 136, 305, 376, 548, 229, 265, 425]
# it was obtained through
# [random.randint(0, 1001) for i in range(20)]

class_weights = [0.4, 0.3, 0.2, 0.1, 0.05, 0.01, 0.005, 0.001, 0.0005]

number_of_objects = np.concatenate([
    np.outer([1e+5], [2**x for x in range(0, 4)]).flatten(),
    np.outer([1e+6], [2**x for x in range(0, 4)]).flatten(),
    np.outer([1e+6], range(10, 51, 5)).flatten()
])


def get_sample(n_objects, positive_class_weight, seed, loc=10):
    """Create a sample from two normal distributions.

    Args:
        n_objects (int): The total number of objects in the sample, i.e. sample size.
        positive_class_weight (float): The proportion of positive objects,
        i.e. the size of the right normal distribution relative to the left one.
        seed (int): A random seed to ensure the reproducibility of normal distributions.
        loc (int): The center of the right normal distribution.
    Returns:
        A tuple consisting of true labels and synthetic classifier scores
        sampled from two normal distributions.

    """
    np.random.seed(seed)
    #
    ld = np.random.normal(loc=0.0, scale=5.0, size=int(n_objects * (1 - positive_class_weight)))
    rd = np.random.normal(loc=loc, scale=5.0, size=int(n_objects * positive_class_weight))
    #
    y_true = [0] * len(ld) + [1] * len(rd)
    d = np.concatenate([ld, rd])
    #
    return y_true, d


def get_metrics(data):
    """Get AUC metrics from the sample generated by `get_sample`.

    Args:
        data (tuple): A tuple containing true labels and synthetic classifier scores.
    Returns:
        A tuple of AUC ROC and AUC PR values according to the input data.

    """
    y_true, d = data
    return roc_auc_score(y_true, d), average_precision_score(y_true, d)


def get_curves(n_objects, class_weight, loc=10):
    """Get data to plot ROC and PR curves using the sample from `get_sample`.

    Args:
        n_objects (int): The number of objects in the sample, i.e. sample size.
        positive_class_weight (float): The proportion of positive objects,
        i.e. the size of the right normal distribution relative to the left one.
        loc (int): The center of the right normal distribution.
    Returns:
        A tuple containing a dictionary of minimum and maximum AUCs,
        FPR, TPR, precision and recall values
        at the `seeds` corresponding to the minimum and maximum AUC ROC values
        during iteration over the `seeds`.

    """
    out = {
        'ROC': {'min': None, 'max': 0.0005},
        'PR': {'min': None, 'max': 0.0005},
    }

    for seed in seeds:
        print('-', end='')
        #
        y_true, d = get_sample(n_objects, class_weight, seed=seed, loc=loc)
        #
        fpr, tpr, _ = roc_curve(y_true, d)
        auc_roc = roc_auc_score(y_true, d)
        #
        precision, recall, _ = precision_recall_curve(y_true, d)
        auc_pr = average_precision_score(y_true, d)
        #
        if out['ROC']['min'] is None or auc_roc < out['ROC']['min']:
            min_fpr, min_tpr = fpr, tpr
            min_precision, min_recall = precision, recall
            out['ROC']['min'] = auc_roc
            out['PR']['min'] = auc_pr
        if auc_roc > out['ROC']['max']:
            max_fpr, max_tpr = fpr, tpr
            max_precision, max_recall = precision, recall
            out['ROC']['max'] = auc_roc
            out['PR']['max'] = auc_pr

    return (
        out,
        min_fpr, max_fpr, min_tpr, max_tpr,
        min_recall, max_recall, min_precision, max_precision
    )


def plot_curves(
    out,
    min_fpr, max_fpr, min_tpr, max_tpr,
    min_recall, max_recall, min_precision, max_precision
):
    """Plot ROC and PR curves using the output of `get_curves` as input data.

    Args:
        out (dict): A dictionary containing the minimum and maximum values of AUC ROC and AUC PR.
        min_fpr (list): Vector of false positive rates corresponding to the minimum AUC ROC value.
        max_fpr (list): Vector of false positive rates corresponding to the maximum AUC ROC value.
        min_tpr (list): Vector of true positive rates corresponding to the minimum AUC ROC value.
        max_tpr (list): Vector of true positive rates corresponding to the maximum AUC ROC value.
        min_recall (list): Vector of recall values corresponding to the minimum AUC ROC value.
        max_recall (list): Vector of recall values corresponding to the maximum AUC ROC value.
        min_precision (list): Vector of precision values corresponding to the minimum AUC ROC value.
        max_precision (list): Vector of precision values corresponding to the maximum AUC ROC value.
    Returns:
        None

    """
    _, axis = plt.subplots(1, 2, figsize=(14, 7))
    #
    axis[0].plot(min_fpr, min_tpr, '--', color='silver', label='AUC ROC min: {:.4f}'.format(out['ROC']['min']))
    axis[0].plot(max_fpr, max_tpr, '--', color='black', label='AUC ROC max: {:.4f}'.format(out['ROC']['max']))
    axis[0].set_ylabel('TPR')
    axis[0].set_xlabel('FPR')
    #
    axis[1].plot(min_recall, min_precision, '--', color='silver', label='AUC PR min: {:.4f}'.format(out['PR']['min']))
    axis[1].plot(max_recall, max_precision, '--', color='black', label='AUC PR max: {:.4f}'.format(out['PR']['max']))
    axis[1].set_ylabel('Precision')
    axis[1].set_xlabel('Recall')
    #
    for idx, metric in enumerate(['ROC', 'PR']):
        axis[idx].legend()
        axis[idx].grid(True, alpha=0.3, aa=True, ls=':', lw=1.1)
        _ = axis[idx].set_title('AUC {0} range: {1:.2f}%'.format(
            metric,
            (out[metric]['max'] * 100 / out[metric]['min']) - 100)
        )
    plt.tight_layout(pad=2)
