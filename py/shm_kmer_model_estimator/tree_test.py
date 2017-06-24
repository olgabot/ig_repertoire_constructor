import os

import numpy as np
from scipy.stats import mannwhitneyu

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from config.config import config, read_config
from config.parse_input_args import parse_args

from shm_kmer_model import cab_shm_model, yale_model, cab_shm_simple_frequency
from mutation_strategies import mutation_strategies
from chains.chains import Chains

from shm_kmer_model.cab_shm_model import Region
from likelihood_calculator.likelihood_calculator import LikelihoodCalculator

from tree_test_utilities import flu_trees_statistics_calculator, tree_test_utilities

from special_utils.os_utils import smart_mkdir


def run_tree_test_chain_strategy(strategy, chain_type, log_dir):
    ymodel                  = yale_model.YaleSHM_Model()
    cabmodel                = cab_shm_model.CAB_SHM_Model(strategy, chain_type)
    cab_sfreq_all_model = cab_shm_simple_frequency.CAB_SHM_SimpleFrequencyModel(strategy, chain_type, functionality='all')
    cab_sfreq_non_model = cab_shm_simple_frequency.CAB_SHM_SimpleFrequencyModel(strategy, chain_type, functionality='nonproductive')

    flu_trees_paths = flu_trees_statistics_calculator.get_flu_trees_paths(chain_type=chain_type)
    tester = tree_test_utilities.TreeTester()
    yresults                  = tester.get_likelihood_statistics_trees(model=ymodel,
                                                                       tree_paths=flu_trees_paths)
    cabresults                = tester.get_likelihood_statistics_trees(model=cabmodel,
                                                                       tree_paths=flu_trees_paths)
    cab_sfreq_all_results = tester.get_likelihood_statistics_trees(model=cab_sfreq_all_model,
                                                                       tree_paths=flu_trees_paths)
    cab_sfreq_non_results = tester.get_likelihood_statistics_trees(model=cab_sfreq_non_model,
                                                                       tree_paths=flu_trees_paths)

    filename = '%s_%s.' % (strategy.name, chain_type.name)
    log_filename = os.path.join(log_dir, filename + 'log')

    smart_mkdir(log_dir)
    with open(log_filename, 'w') as f:
        f.write("Median for Yale: %lf\n" % np.nanmedian(yresults.accuracies))
        f.write("Median for CAB: %lf\n" % np.nanmedian(cabresults.accuracies))
        f.write("Median for CAB Simple Freq All: %lf\n" % np.nanmedian(cab_sfreq_all_results.accuracies))
        f.write("Median for CAB Simple Freq NonProductive: %lf\n" % np.nanmedian(cab_sfreq_non_results.accuracies))

        f.write("Yale Accuracies: %s\n" % yresults.accuracies)
        f.write("CAB Accuracies: %s\n" % cabresults.accuracies)
        f.write("CAB Simple Freq All Accuracies: %s\n" % cab_sfreq_all_results.accuracies)
        f.write("CAB Simple Freq NonProductive Accuracies: %s\n" % cab_sfreq_non_results.accuracies)

        f.write("Full accuracy for Yale: %lf\n" % yresults.full_accuracy)
        f.write("Full accuracy for CAB: %lf\n" % cabresults.full_accuracy)
        f.write("Full accuracy for CAB All: %lf\n" % cab_sfreq_all_results.full_accuracy)
        f.write("Full accuracy for CAB NonProductive: %lf\n" % cab_sfreq_non_results.full_accuracy)

        mw_ycab = mannwhitneyu(yresults.accuracies, cabresults.accuracies, use_continuity=True)
        f.write("Mann Whitney test for equality of means Yale vs CAB: %s\n" % str(mw_ycab))

        mw_ycabsfa = mannwhitneyu(yresults.accuracies, cab_sfreq_all_results.accuracies, use_continuity=True)
        f.write("Mann Whitney test for equality of means Yale vs CAB Simple Freq All: %s\n" % str(mw_ycabsfa))

        mw_ycabsfn = mannwhitneyu(yresults.accuracies, cab_sfreq_non_results.accuracies, use_continuity=True)
        f.write("Mann Whitney test for equality of means Yale vs CAB Simple Freq NonProductive: %s\n" % str(mw_ycabsfn))

        mw_cabcabsfa = mannwhitneyu(cabresults.accuracies, cab_sfreq_all_results.accuracies, use_continuity=True)
        f.write("Mann Whitney test for equality of means CAB vs CAB Simple Freq All: %s\n" % str(mw_cabcabsfa))

        mw_cabcabsfn = mannwhitneyu(cabresults.accuracies, cab_sfreq_non_results.accuracies, use_continuity=True)
        f.write("Mann Whitney test for equality of means CAB vs CAB Simple Freq NonProductive: %s\n" % str(mw_cabcabsfn))

    def draw(title, yale, cab, cabsfa, cabsfn, fig_filename, bins=10):
        def draw_distplot(x, color):
            return sns.distplot(x[~np.isnan(x)], color=color, bins=bins, rug=True, kde=True, hist=False)
        ypict = draw_distplot(yale.accuracies, color='blue')
        cabpict = draw_distplot(cab.accuracies, color='green')
        cabnpict = draw_distplot(cab_sfreq_all_results.accuracies, color='red')
        cabnpict = draw_distplot(cab_sfreq_non_results.accuracies, color='black')
        plt.legend(['Yale', 'CAB', 'CAB Simple Freq All', 'CAB Simple Freq NonProd'])
        ax = plt.gca()
        leg = ax.get_legend()
        leg.legendHandles[0].set_color('blue')
        leg.legendHandles[1].set_color('green')
        leg.legendHandles[2].set_color('red')
        leg.legendHandles[3].set_color('black')
        plt.title(title)
        plt.savefig(fig_filename, format='pdf')
        plt.clf()

    figures_dir = os.path.join(log_dir, 'figures')
    smart_mkdir(figures_dir)
    draw('Accuracy', yresults, cabresults, cab_sfreq_all_model, cab_sfreq_non_results,
          os.path.join(figures_dir, filename) + "pdf")
    return {'Yale': yresults, 'CAB': cabresults, 'CAB_SF_all': cab_sfreq_all_model, 'CAB_SF_nonprod': cab_sfreq_non_results}


def main():
    parsed_args = parse_args()
    input_config = read_config(parsed_args.input)
    test_config = input_config.kmer_model_tree_test
    for strategy in mutation_strategies.MutationStrategies:
        for chain_type in Chains:
            if chain_type.name == 'IG':
                continue
            print(strategy, chain_type.name)
            run_tree_test_chain_strategy(strategy, chain_type, test_config.outdir)



if __name__ == "__main__":
    main()
